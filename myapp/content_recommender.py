# myapp/content_recommender.py

import random
from .models import Articles as Article
from .models import UserInteraction  # Using existing model

# Alias UserInteraction to UserReadingData
UserReadingData = UserInteraction
class ContentRecommender:
    def __init__(self, user):
        self.user = user

    def get_average_reading_speed(self):
        reading_data = UserReadingData.objects.filter(user=self.user)
        if reading_data.exists():
            total_speed = sum([entry.reading_speed_wpm for entry in reading_data])
            return total_speed / reading_data.count()
        return 200  # default average reading speed in words per minute

    def recommend_articles(self, limit=5):
        avg_speed = self.get_average_reading_speed()

        # Define thresholds
        if avg_speed < 150:
            target_length = 'short'
        elif avg_speed > 250:
            target_length = 'long'
        else:
            target_length = 'medium'

        # Get articles based on estimated reading time
        articles = Article.objects.all()
        filtered_articles = []

        for article in articles:
            word_count = len(article.content.split())
            estimated_time = word_count / avg_speed

            if target_length == 'short' and estimated_time <= 2:
                filtered_articles.append(article)
            elif target_length == 'medium' and 2 < estimated_time <= 5:
                filtered_articles.append(article)
            elif target_length == 'long' and estimated_time > 5:
                filtered_articles.append(article)

        # Return a few random articles from the filtered list
        return random.sample(filtered_articles, min(limit, len(filtered_articles)))
