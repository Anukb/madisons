from .models import Articles, UserInteraction, UserViewedArticle, UserEngagement, UserPreferences
from django.db.models import Avg, Count

def get_recommendations(user):
    # Try to fetch user preferences
    try:
        preferences = UserPreferences.objects.get(user=user)
        preferred_categories = preferences.preferred_categories.all()
    except UserPreferences.DoesNotExist:
        # If no preferences exist, return an empty queryset or a default set of articles
        return Articles.objects.none()  # or return a default set of articles

    # Fetch articles based on preferred categories and published status
    recommended_articles = Articles.objects.filter(
        category__in=preferred_categories,
        status="published"
    ).annotate(
        views_count=Count('userinteraction')
    ).order_by('-views_count')[:5]  # Top 5 articles

    return recommended_articles

def collaborative_filtering(user, recent_interactions):
    # Fetch user engagement history
    engaged_articles = UserEngagement.objects.filter(user=user).values_list('article', flat=True)
    print(f"Engaged articles: {engaged_articles}")
    
    # Find similar users based on articles they have engaged with
    similar_users = UserEngagement.objects.filter(article__in=engaged_articles).exclude(user=user).values('user').distinct()
    print(f"Similar users: {similar_users}")
    
    # Recommend articles that similar users have engaged with, excluding already engaged articles
    similar_articles = Articles.objects.filter(userengagement__user__in=similar_users).exclude(id__in=engaged_articles)
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
    tags = Articles.objects.filter(id__in=viewed_articles).values_list('tags', flat=True)
    print(f"Tags: {tags}")
    
    # Recommend articles based on categories and tags, only published articles
    recommendations = Articles.objects.filter(
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
    recommended = Articles.objects.filter(
        category__in=user_preferences,
        status="published"
    )[:5]
    return recommended