from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# from myapp.models import UserSearchHistory  # Removed to avoid circular import
import uuid
from django.db.models import Avg
from datetime import timedelta
from django.utils.text import slugify
from django.urls import reverse
import math
from django.utils.html import strip_tags

class Register(models.Model):
    reg_id = models.AutoField(primary_key=True)  # Primary key for Register
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    confirm_password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return self.username

class Login(models.Model):
    log_id = models.AutoField(primary_key=True)  # Primary key for Login
    reg_id = models.ForeignKey(Register, on_delete=models.CASCADE,)  # Foreign key to Register
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.email

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Articles(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles_alt')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')  # Add status field
    image = models.ImageField(upload_to='articles/', null=True, blank=True)  # Add image field
    pdf_file = models.FileField(upload_to='articles/pdfs/', null=True, blank=True) # Add PDF field
    created_at = models.DateTimeField(auto_now_add=True)
    match_score = models.FloatField(null=True, blank=True)  # Stores AI match percentage

    def __str__(self):
        return self.title

    def average_rating(self):
        return self.ratings.aggregate(Avg('score'))['score__avg'] or 0

    def save(self, *args, **kwargs):
        if self.content:
            self.word_count = len(self.content.split())

        if self.word_count and not self.match_score:
            self.match_score = min(100, max(70, (self.word_count / 1000) * 30 + 70))

        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'article_id': self.id, 'slug': self.slug})
class Tag(models.Model):
    name = models.CharField(max_length=50)
class UserReadingData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    time_spent = models.PositiveIntegerField(help_text="Time spent in seconds")
    last_read = models.DateTimeField(auto_now=True)
    is_bookmarked = models.BooleanField(default=False)
    scroll_depth = models.FloatField(default=0.0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'article')
        indexes = [
            models.Index(fields=['user', 'last_read']),
            models.Index(fields=['article', 'time_spent'])
        ]

    def __str__(self):
        return f"{self.user.username}'s interaction with {self.article.title}"

class UserReadingProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    average_reading_speed_wpm = models.FloatField(default=200)  # words per minute
    preferred_reading_level = models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Advanced')], default=2)
    preferred_tags = models.ManyToManyField(Tag)
    last_updated = models.DateTimeField(auto_now=True)
def update_reading_speed(self, new_wpm):
        # Weighted average to gradually adjust reading speed
        if self.average_reading_speed_wpm:
            self.average_reading_speed_wpm = (self.average_reading_speed_wpm * 0.7) + (new_wpm * 0.3)
        else:
            self.average_reading_speed_wpm = new_wpm
        self.save()

class ReadingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    scroll_depth = models.FloatField(default=0)  # percentage
    words_per_minute = models.FloatField(null=True, blank=True)
    time_spent = models.FloatField(null=True, blank=True)  # in seconds
    def calculate_wpm(self):
        if self.time_spent and self.article.word_count:
            minutes = self.time_spent / 60
            return self.article.word_count / minutes if minutes > 0 else 0
        return None

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.time_spent = (self.end_time - self.start_time).total_seconds()
            self.words_per_minute = self.calculate_wpm()
        super().save(*args, **kwargs)
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('article', 'New Article'),
        ('comment', 'New Comment'),
        ('announcement', 'Announcement'),
        ('subscription', 'Subscription Update')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    title = models.CharField(max_length=255, null=True, blank=True)  # Make nullable for backward compatibility
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, null=True, blank=True)  # Make nullable
    related_link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models

class Plan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    features = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)  # Not auto_now_add initially
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} (${self.price})"
    def get_savings_percentage(self):
        """Calculate savings percentage for longer plans"""
        if "6 month" in self.name.lower():
            monthly_plan = Plan.objects.filter(name__icontains="premium", duration_days=30).first()
            if monthly_plan:
                monthly_cost = monthly_plan.price * 6
                savings = ((monthly_cost - self.price) / monthly_cost) * 100
                return round(savings)
        return 0
    @property
    def price_in_paise(self):
        """Convert price to paise for Razorpay"""
        return int(self.price * 100)
    
    def get_duration_display(self):
        """Human-readable duration"""
        if self.duration_days == 30:
            return "1 Month"
        elif self.duration_days == 180:
            return "6 Months"
        elif self.duration_days == 365:
            return "1 Year"
        return f"{self.duration_days} days"
    def get_features_list(self):
        """Convert features JSON to list"""
        features = []
        if self.features.get('read_articles'):
            features.append("Read all articles")
        if self.features.get('comment'):
            features.append("Comment on articles")
        if self.features.get('ad_free'):
            features.append("Ad-free experience")
        if self.features.get('exclusive_content'):
            features.append("Exclusive content")
        if self.features.get('offline_reading'):
            features.append("Offline reading")
        if self.features.get('priority_support'):
            features.append("Priority support")
        return features

class UserPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} subscription"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)  # Use timezone.now()
        super().save(*args, **kwargs)

    def check_is_active(self):
        """Checks if the subscription is currently active based on end_date."""
        now = timezone.now()
        if self.end_date >= now:
            if not self.is_active:
                self.is_active = True
                self.save()
            return True
        else:
            if self.is_active:
                self.is_active = False
                self.save()
            return False

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.check_is_active()  # Check status on save
        super().save(*args, **kwargs)

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} read {self.article.title} at {self.timestamp}"

class Transaction(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username}'s payment for {self.plan.name}"

class UserSearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.search_term}"

class UserViewedArticle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Articles, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp

    def __str__(self):
        return f"{self.user.username} viewed {self.article.title}"

class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey('Articles', on_delete=models.CASCADE)
    time_spent = models.FloatField()  # Time spent on the article in seconds
    reading_speed = models.FloatField(default=0)  # Reading speed in words per minute
    viewed_at = models.DateTimeField(auto_now_add=True)
    interaction_type = models.CharField(max_length=100, default='default_value')  # Replace 'default_value' with a sensible default
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=0)  # time spent in seconds
    scroll_depth = models.FloatField(default=0.0)
    is_bookmarked = models.BooleanField(default=False)  
    class Meta:
        unique_together = ('user', 'article', 'interaction_type')
    def __str__(self):
        return f"{self.user.username} - {self.article.title}"

class UserEngagement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey('Articles', on_delete=models.CASCADE)
    liked = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    bookmarked = models.BooleanField(default=False)
    commented = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} engaged with {self.article.title}"

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_categories = models.ManyToManyField('Category', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Preferences"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg')  # Default image

    def __str__(self):
        return self.user.username

class Comment(models.Model):
    article = models.ForeignKey(Articles, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.article.title}'

class Rating(models.Model):
    article = models.ForeignKey('Articles', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()  # Assuming a score from 1 to 5
    review = models.TextField(blank=True, null=True)  # Optional review text
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'user')  # Ensure one rating per user per article

    def __str__(self):
        return f'{self.user.username} rated {self.article.title} - {self.score}'


class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Complaint by {self.user.username}: {self.subject}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='upcoming')

    def __str__(self):
        return self.title

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)  # e.g., 'view_article', 'like_article'
    timestamp = models.DateTimeField(auto_now_add=True)

class ArticleView(models.Model):
    article = models.ForeignKey('Articles', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    view_time = models.DateTimeField(auto_now_add=True)

class Engagement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey('Articles', on_delete=models.CASCADE)
    liked = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    commented = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class AdminLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField()
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.action} - {self.target_model}"

class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved')
    ]

    article = models.ForeignKey(Articles, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='resolved_reports'
    )

    def __str__(self):
        return f"Report for {self.article.title} by {self.reporter.username}"

    class Meta:
        ordering = ['-created_at']

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles_main')
    description = models.TextField(blank=True, null=True)
    content = models.TextField()
    pdf_file = models.FileField(upload_to='article_pdfs/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles_main_category')
    tags = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to='article_images/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_publish_time = models.DateTimeField(null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    moderator_notes = models.TextField(blank=True, null=True)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    meta_description = models.CharField(max_length=160, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
    read_time = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    reading_level = models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Advanced')], default=1)
    word_count = models.IntegerField(default=0)
    tags = models.ManyToManyField('Tag')
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='article_groups_relation',
        blank=True,
        help_text=(
            'The groups this article belongs to. A article will get all permissions '
            'granted to each of their groups.'
        ),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='article_permissions_relation',
        blank=True,
        help_text='Specific permissions for this article.',
        verbose_name='user permissions',
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1

        if self.content:
            word_count = len(strip_tags(self.content).split())
            self.read_time = math.ceil(word_count / 200)
        else:
            self.read_time = 0
            
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('article_detail', args=[str(self.id), self.slug])

    def __str__(self):
        return self.title

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
def activate(self):
        with transaction.atomic():
            # Deactivate previous subscriptions
            Subscription.objects.filter(user=self.user, active=True).update(active=False)
            
            # Set activation details
            self.active = True
            self.activated_at = timezone.now()
            self.save()
            
            # Create UserPlan
            UserPlan.objects.create(
                user=self.user,
                plan=self.plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=self.plan.duration_days),
                is_active=True
            )
def __str__(self):
        return f"{self.user.username}'s {self.plan.name} subscription"

class Meta:
        ordering = ['-created_at']
class SubscriptionDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        logger.info(f"Incoming request: {request.method} {request.path}")
        response = self.get_response(request)
        logger.info(f"Outgoing response: {response.status_code}")
        return response