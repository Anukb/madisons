# utils.py (Recommendation Engine)
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class ContentRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.article_vectors = None
        
    def train(self, articles):
        """Train the recommendation model on articles"""
        texts = [f"{article.title} {article.content[:500]}" for article in articles]
        self.article_vectors = self.vectorizer.fit_transform(texts)
        
    def recommend(self, user, articles, user_profile, reading_sessions, top_n=5):
        """Generate recommendations based on reading speed and preferences"""
        if not self.article_vectors:
            self.train(articles)
            
        # Calculate reading speed if we have recent sessions
        recent_sessions = reading_sessions.filter(user=user).order_by('-start_time')[:5]
        if recent_sessions:
            total_words = sum(s.article.word_count * (s.scroll_depth/100) for s in recent_sessions)
            total_time = sum(s.time_spent for s in recent_sessions if s.time_spent)
            if total_time > 0:
                current_speed_wpm = (total_words / total_time) * 60
                # Update user profile with exponential moving average
                user_profile.average_reading_speed_wpm = (
                    0.7 * user_profile.average_reading_speed_wpm + 
                    0.3 * current_speed_wpm
                )
                user_profile.save()
        
        # Filter articles by reading level and preferred tags
        preferred_tags = user_profile.preferred_tags.all()
        candidate_articles = [
            a for a in articles 
            if a.reading_level <= user_profile.preferred_reading_level and
            (not preferred_tags or a.tags.filter(id__in=[t.id for t in preferred_tags]).exists())
        ]
        
        # Estimate reading time for each article
        for article in candidate_articles:
            article.estimated_reading_time = (article.word_count / user_profile.average_reading_speed_wpm) * 60
            
        # Sort by estimated reading time closest to user's average session time
        avg_session_time = np.mean([s.time_spent for s in recent_sessions if s.time_spent]) if recent_sessions else 300
        candidate_articles.sort(key=lambda x: abs(x.estimated_reading_time - avg_session_time))
        
        return candidate_articles[:top_n]