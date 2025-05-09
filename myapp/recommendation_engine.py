from .models import Article, UserInteraction, UserViewedArticle, UserEngagement, UserPreferences
from django.db.models import Avg, Count

def get_recommendations(user):
    # Try to fetch user preferences
    try:
        preferences = UserPreferences.objects.get(user=user)
        preferred_categories = preferences.preferred_categories.all()
    except UserPreferences.DoesNotExist:
        # If no preferences exist, return an empty queryset or a default set of articles
        return Article.objects.none()  # or return a default set of articles

    # Fetch articles based on preferred categories and published status
    recommended_articles = Article.objects.filter(
        category__in=preferred_categories,
        status="published"
    ).annotate(
        views_count=Count('userinteraction')
    ).order_by('-views_count')[:5]  # Top 5 articles

    return recommended_articles
class ContentRecommender:
    def __init__(self):
        self.max_speed_diff = 50  # Max allowed WPM difference
        self.min_confidence = 0.6  # Minimum confidence score
    
    def recommend(self, user, articles, profile, reading_sessions, top_n=5):
        """
        Recommend articles based on reading speed and preferences
        """
        # Get articles with similar reading level
        suitable_articles = articles.filter(
            reading_level__lte=profile.preferred_reading_level + 1,
            status='published'
        ).exclude(
            Q(id__in=[s.article.id for s in reading_sessions])
        )
        
        # Score articles based on reading speed match
        scored_articles = []
        for article in suitable_articles:
            # Calculate expected reading time based on user's speed
            expected_time = (article.word_count / profile.average_reading_speed_wpm) * 60
            
            # Score based on how close article is to user's preferred length
            # (Assuming we have some length preference in profile)
            length_score = 1 - min(1, abs(article.word_count - 1500) / 3000)
            
            # Combine scores
            total_score = length_score * 0.7
            
            # Add category preference if available
            if hasattr(user, 'userpreferences'):
                if article.category in user.userpreferences.preferred_categories.all():
                    total_score += 0.3
            
            scored_articles.append((article, total_score))
        
        # Sort by score and return top N
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return [article for article, score in scored_articles[:top_n]]
def collaborative_filtering(user, recent_interactions):
    # Fetch user engagement history
    engaged_articles = UserEngagement.objects.filter(user=user).values_list('article', flat=True)
    print(f"Engaged articles: {engaged_articles}")
    
    # Find similar users based on articles they have engaged with
    similar_users = UserEngagement.objects.filter(article__in=engaged_articles).exclude(user=user).values('user').distinct()
    print(f"Similar users: {similar_users}")
    
    # Recommend articles that similar users have engaged with, excluding already engaged articles
    similar_articles = Article.objects.filter(userengagement__user__in=similar_users).exclude(id__in=engaged_articles)
    print(f"Similar articles: {similar_articles}")
    
    return similar_articles[:5]

def content_based_filtering(user, recent_interactions):
    # Fetch user interactions to analyze preferences
    user_interactions = UserInteraction.objects.filter(user=user)
    print(f"User interactions: {user_interactions}")
    
    # Fetch user reading history
    viewed_articles = UserViewedArticle.objects.filter(user=user).values_list('article', flat=True)
    print(f"Viewed articles: {viewed_articles}")
    
    # Example logic for content-based filtering using existing fields
    categories = user_interactions.values_list('article__category', flat=True).distinct()
    print(f"Categories: {categories}")
    
    # Fetch tags from previously viewed articles
    tags = Article.objects.filter(id__in=viewed_articles).values_list('tags', flat=True)
    print(f"Tags: {tags}")
    
    # Recommend articles based on categories and tags, only published articles
    recommendations = Article.objects.filter(
        category__in=categories,
        status="published"
    ).exclude(id__in=viewed_articles)
    print(f"Recommendations before tag filtering: {recommendations}")
    # Further filter based on tags if available
    if tags:
        recommendations = recommendations.filter(tags__in=tags)
        print(f"Recommendations after tag filtering: {recommendations}")
    
    return recommendations[:5]

def recommend_articles(user):
    user_preferences = user.userpreferences.preferred_categories.all()
    recommended = Article.objects.filter(
        category__in=user_preferences,
        status="published"
    )[:5]
    return recommended