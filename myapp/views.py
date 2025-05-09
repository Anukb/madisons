from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from .models import Category, Articles, UserSearchHistory, UserViewedArticle, UserInteraction, UserPreferences, Profile, Comment, Rating, Notification, Event, Complaint, UserActivity, AdminLog, Report, ArticleView, Engagement, Announcement
import json
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError
from .models import Plan, UserPlan, Transaction, Subscription
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.db.models import Count, Q, Avg, F
from .recommendation_engine import get_recommendations, collaborative_filtering, content_based_filtering  # Assume this is your ML model
from django.views.decorators.csrf import csrf_exempt
from .forms import CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
import os
from transformers import pipeline
import csv
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
import logging
from .models import Articles
from .models import Event
from .models import Complaint
from .models import ReadingHistory
import re
from django.utils.text import slugify
from django.db import transaction as db_transaction # Avoid naming conflict
from .decorators import subscription_required # Import the decorator
import bleach # For content sanitization (pip install bleach)
from datetime import datetime
import stripe # Add stripe import
from django.views.decorators.csrf import csrf_exempt # For webhook
from django.db import transaction as db_transaction # For atomic operations
from django.urls import reverse_lazy
import razorpay
import time
from .models import ReadingSession, UserReadingProfile
from .content_recommender import ContentRecommender

os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Force CPU usage

# Initialize the summarization pipeline globally for better performance
try:
    summarizer = pipeline("summarization", 
                         model="sshleifer/distilbart-cnn-12-6", 
                         max_length=50, 
                         min_length=20,
                         device=-1)  # Force CPU usage
except Exception as e:
    print(f"Warning: Could not load summarizer model: {e}")
    summarizer = None

# Replace the summarizer initialization with a simple function
def simple_summarize(text, max_sentences=3):
    """Simple summarization by taking first few sentences"""
    # Split text into sentences (basic approach)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    # Take first few sentences
    summary = '. '.join(sentences[:max_sentences]) + '.'
    return summary

def edit_profile_view(request):
    profile = request.user.profile  # Assuming Profile is linked to User via a OneToOneField

    if request.method == 'POST':
        # Retrieve and validate User fields
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()  # Ensure email is retrieved and stripped

        if not email:
            messages.error(request, 'Email is required.')  # Add an error message if email is empty
            return render(request, 'account/profile.html', {'profile': profile})  # Render profile with error

        # Update User fields
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email  # Now safe to assign

        # Update Profile fields
        profile.user_type = request.POST.get('user_type')
        profile.bio = request.POST.get('bio')

        # Save the updates
        request.user.save()
        profile.save()

        messages.success(request, 'Your profile has been updated!')
        
        # Render the profile page with updated data
        return render(request, 'account/profile.html', {'profile': profile})

    return render(request, 'account/edit_profile.html', {'profile': profile})
@login_required
def profile_view(request):
    user_preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    profile, created = Profile.objects.get_or_create(user=request.user)
    submissions = Articles.objects.filter(author=request.user).exclude(status='published').order_by('-created_at')

    if request.method == 'POST':
        try:
            # Update user fields
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.save()

            # Update profile picture
            if 'profile_pic' in request.FILES:
                profile.profile_pic = request.FILES['profile_pic']
                profile.save()

            # Update preferences
            category_ids = request.POST.getlist('interests')
            user_preferences.preferred_categories.set(category_ids)

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    return render(request, 'profile.html', {
        'user': request.user,
        'categories': Category.objects.all(),
        'user_preferences': user_preferences,
        'profile': profile
    })
def home_view(request):
    # Only fetch published articles
    articles = Articles.objects.all().order_by('-created_at')[:6]
    return render(request, 'home.html', {'articles': articles})
    recommendations = []
    if request.user.is_authenticated:
        try:
            profile = UserReadingProfile.objects.get(user=request.user)
            sessions = ReadingSession.objects.filter(user=request.user)
            recommender = ContentRecommender()
            recommendations = recommender.recommend(
                request.user, 
                Article.objects.all(), 
                profile, 
                sessions,
                top_n=3
            )
        except UserReadingProfile.DoesNotExist:
            pass
    
    context = {
        'articles': articles,
        'recommendations': recommendations,
    }
    return render(request, 'home.html', context)

def welcome_notification(user):
    """Create a welcome notification for new users"""
    return Notification.objects.create(
        user=user,
        title="Welcome to Madison!",
        message="Welcome to Madison! We're excited to have you join our community. Start exploring articles or write your own to share your knowledge.",
        notification_type='welcome',
        is_read=False
    )

# --- Define Validation Constants ---
TITLE_REGEX = r"^[A-Za-z\s\-]+$" # Allow letters, spaces, hyphens
MAX_TITLE_LENGTH = 100
DESCRIPTION_REGEX = r"^[A-Za-z0-9\s.,!?'\"()-]+$" # Allow letters, numbers, basic punctuation
MAX_DESCRIPTION_LENGTH = 250
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
MAX_IMAGE_SIZE_MB = 2
MAX_UPLOAD_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_PDF_EXTENSIONS = ['pdf']
MAX_PDF_SIZE_MB = 5 # Example
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

# --- Helper Validation Functions ---
def validate_file_size(value, max_size_bytes):
    if value.size > max_size_bytes:
        raise ValidationError(f"File size cannot exceed {max_size_bytes / 1024 / 1024:.1f}MB.")

def validate_schedule_time(dt_value):
     if dt_value and dt_value <= timezone.now():
          raise ValidationError("Scheduled publish time cannot be in the past.")

def register(request):
    context = {}
    errors = {}  # Initialize errors here

    # Initialize variables to avoid UnboundLocalError
    username = ''
    email = ''
    password1 = ''
    password2 = ''
    full_name = ''
    country = ''
    bio = ''
    profile_picture = None

    if request.method == 'POST':
        # User fields
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Profile fields
        full_name = request.POST.get('full_name', '').strip()
        country = request.POST.get('country', '').strip()
        bio = request.POST.get('bio', '').strip()
        profile_picture = request.FILES.get('profile_picture')

        # Validation
        is_valid = True
        errors = {}

        if not username:
            errors['username'] = "Username is required."
            is_valid = False
        elif User.objects.filter(username=username).exists():
            errors['username'] = "Username is already taken."
            is_valid = False

        if not email:
            errors['email'] = "Email is required."
            is_valid = False
        else:
            try:
                validate_email(email)
                if User.objects.filter(email=email).exists():
                    errors['email'] = "Email is already registered."
                    is_valid = False
            except ValidationError:
                errors['email'] = "Invalid email format."
                is_valid = False

        if not password1 or not password2:
            errors['password'] = "Both passwords are required."
            is_valid = False
        elif password1 != password2:
            errors['password'] = "Passwords do not match."
            is_valid = False
        elif len(password1) < 8:
            errors['password'] = "Password must be at least 8 characters."
            is_valid = False

        if not full_name:
            errors['full_name'] = "Full name is required."
            is_valid = False

        if not country:
            errors['country'] = "Country is required."
            is_valid = False

        if is_valid:
            user = User.objects.create_user(username=username, email=email, password=password1)
            profile = UserProfile.objects.create(
                user=user,
                full_name=full_name,
                country=country,
                bio=bio,
                profile_picture=profile_picture
            )

        Notification.objects.create(
            user=user,
            title="Welcome to Madison!",
            message="Thank you for joining Madison. Start exploring articles and connecting with other readers!",
            notification_type='welcome'
        )

        messages.success(request, f"Welcome, {full_name}! Your Madison profile is ready.")
        return redirect('login')

        context['errors'] = errors
        context['input'] = {
                'username': username,
                'email': email,
                'full_name': full_name,
                'country': country,
                'bio': bio
            }

    return render(request, 'account/register.html', context)

def check_username(request):
    username = request.GET.get('username')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})  # Return a JSON response with the existence status

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                # Create a test notification - Fix indentation here
                Notification.objects.create(
                    user=user,
                    title="Welcome Back!",
                    message=f"Welcome back to Madison Magazine, {user.username}!",
                    is_read=False
                )
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email address.')

    return render(request, 'account/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate a password reset link/token (you can customize this part)
            token = get_random_string(length=32)
            # Save the token to the user model or handle it as you need
            
            # Send email with reset link
            reset_link = f"http://yourdomain.com/reset-password/{token}/"  # Update with your domain
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Password reset email has been sent.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email address.')

    return render(request, 'account/forgot_password.html', {})  # Updated template path

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check if the credentials are correct
        if username == "admin@gmail.com" and password == "admin":
            try:
                admin_user = User.objects.get(username='admin')
            except User.DoesNotExist:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@gmail.com',
                    password='admin'
                )
            
            # Log in the admin user
            login(request, admin_user)
            return redirect('admin_dashboard')  # This will now use the custom-admin URL
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, "account/admin_login.html")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')

    # Get query parameters for filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Get users for user management section
    users = User.objects.select_related('profile').exclude(is_superuser=True).order_by('-date_joined')
    
    # Get events for events section
    events = Event.objects.select_related('created_by').order_by('-date')
    
    # Apply filters if in user management section
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if status_filter:
        users = users.filter(is_active=(status_filter == 'active'))

    # Get real-time statistics for dashboard
    total_users = User.objects.exclude(is_superuser=True).count()
    active_users = User.objects.exclude(is_superuser=True).filter(is_active=True).count()
    blocked_users = total_users - active_users  # Perform the subtraction here
    
    context = {
        # User Statistics
        'total_users': total_users,
        'active_users': active_users,
        'blocked_users': blocked_users,  # Pass the result to the template
        'new_users_today': User.objects.exclude(is_superuser=True).filter(date_joined__date=timezone.now().date()).count(),
        'all_users': users,  # Add users to context
        'search_query': search_query,
        'status_filter': status_filter,
        
        # Content Statistics
        'total_articles': Articles.objects.count(),
        'pending_articles': Articles.objects.filter(status='draft').count(),
        'published_articles': Articles.objects.filter(status='published').count(),
        
        # Event Statistics
        'active_events': Event.objects.filter(status='upcoming').count(),
        'total_events': Event.objects.count(),
        'events': events,  # Add events to context
        # Complaint Statistics
        'open_complaints': Complaint.objects.filter(status='pending').count(),
        'total_complaints': Complaint.objects.count(),
        
        # Recent Activity
        'recent_articles': Articles.objects.select_related('author', 'category').order_by('-created_at')[:5],
        'recent_users': User.objects.exclude(is_superuser=True).order_by('-date_joined')[:5],
        'recent_complaints': Complaint.objects.select_related('user').order_by('-created_at')[:5],
        
        # Analytics Data
        'user_growth': User.objects.exclude(is_superuser=True).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')[:7],
        
        'content_distribution': {
            'articles': Articles.objects.count(),
            'comments': Comment.objects.count(),
            'events': Event.objects.count()
        },
        'categories': Category.objects.all()  # Add categories to context
    }
    
    return render(request, 'account/admin_dashboard.html', context)
# views.py

@login_required
def reading_history(request):
    sessions = ReadingSession.objects.filter(user=request.user).select_related('article').order_by('-start_time')
    return render(request, 'reading_history.html', {'sessions': sessions})
@login_required
def admin_user_management(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get query parameters for filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset with related data - exclude superusers/admin
    users = User.objects.select_related('profile').exclude(is_superuser=True).order_by('-date_joined')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if status_filter:
        users = users.filter(is_active=(status_filter == 'active'))
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context = {
        'users': users,
        'total_users': User.objects.exclude(is_superuser=True).count(),
        'active_users': User.objects.exclude(is_superuser=True).filter(is_active=True).count(),
        'search_query': search_query,
        'status_filter': status_filter
    }
    
    return render(request, 'admin/user_management.html', context)

@login_required
def admin_toggle_user_status(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()

        AdminLog.objects.create(
            admin=request.user,
            action='toggle_status',
            target_model='User',
            target_id=user.id,
            details=f"Changed user status to {'active' if user.is_active else 'inactive'}"
        )

        return JsonResponse({'success': True, 'is_active': user.is_active})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_content_moderation(request):
    articles = Articles.objects.filter(status='pending')  # Adjust the filter as needed
    context = {
        'articles': articles,
    }
    return render(request, 'admin/content_moderation.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_get_article(request, article_id):
    try:
        article = Articles.objects.get(id=article_id)
        data = {
            'id': article.id,
            'title': article.title,
            'description': article.description,
            'content': article.content,
            'author': article.author.username,
            'category': article.category.name,
            'status': article.status,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'image_url': article.image.url if article.image else None
        }
        return JsonResponse(data)
    except Articles.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_approve_article(request, article_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        article = Articles.objects.get(id=article_id)
        article.status = 'published'
        article.save()
        
        # Create notification for the author
        Notification.objects.create(
            user=article.author,
            title='Article Approved',
            message=f'Your article "{article.title}" has been approved and published.',
            notification_type='article_approved'
        )
        
        return JsonResponse({'success': True, 'message': 'Article approved successfully'})
    except Articles.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_reject_article(request, article_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason')
        
        if not reason:
            return JsonResponse({'error': 'Rejection reason is required'}, status=400)
        
        article = Articles.objects.get(id=article_id)
        article.status = 'rejected'
        article.save()
        
        # Create notification for the author
        Notification.objects.create(
            user=article.author,
            title='Article Rejected',
            message=f'Your article "{article.title}" has been rejected. Reason: {reason}',
            notification_type='article_rejected'
        )
        
        return JsonResponse({'success': True, 'message': 'Article rejected successfully'})
    except Articles.DoesNotExist:
        return JsonResponse({'error': 'Article not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def admin_handle_complaint(request, complaint_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        complaint = Complaint.objects.get(id=complaint_id)
        action = request.POST.get('action')
        
        if action == 'review':
            complaint.status = 'reviewed'
        elif action == 'resolve':
            complaint.status = 'resolved'
        
        complaint.admin_notes = request.POST.get('notes', '')
        complaint.save()

        AdminLog.objects.create(
            admin=request.user,
            action=f'handle_complaint_{action}',
            target_model='Complaint',
            target_id=complaint.id,
            details=f"Changed complaint status to {complaint.status}"
        )

        return JsonResponse({'success': True, 'status': complaint.status})
    except Complaint.DoesNotExist:
        return JsonResponse({'error': 'Complaint not found'}, status=404)

@login_required
def admin_event_management(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            date_str = request.POST.get('date')
            is_featured = request.POST.get('is_featured') == 'on'
            
            # Validate required fields
            if not all([title, description, date_str]):
                return JsonResponse({
                    'success': False,
                    'error': 'Please fill in all required fields.'
                })

            # Parse the date string
            try:
                event_date = timezone.datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format.'
                })

            # Create the event
            event = Event.objects.create(
                title=title,
                description=description,
                date=event_date,
                is_featured=is_featured,
                created_by=request.user,
                status='upcoming'
            )

            # Handle image upload
            if request.FILES.get('image'):
                event.image = request.FILES['image']
                event.save()

            # Create notification for all users
            Notification.objects.create(
                user=request.user,
                title='New Event Created',
                message=f'A new event "{title}" has been created.',
                notification_type='event'
            )

            return JsonResponse({
                'success': True,
                'message': 'Event created successfully',
                'event_id': event.id
            })

        except Exception as e:
            print(f"Error creating event: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while creating the event.'
            })

    # GET request - return list of events
    events = Event.objects.all().order_by('-date')
    return JsonResponse({
        'events': [{
            'id': event.id,
            'title': event.title,
            'date': event.date.strftime('%Y-%m-%d %H:%M'),
            'status': event.status,
            'is_featured': event.is_featured,
            'image_url': event.image.url if event.image else None
        } for event in events]
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_analytics(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Gather user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=30)).count()
        
    # Gather content statistics
    total_articles = Articles.objects.count()
    published_articles = Articles.objects.filter(status='published').count()
    pending_articles = Articles.objects.filter(status='draft').count()

    # Gather engagement statistics
    total_comments = Comment.objects.count()
    total_views = UserViewedArticle.objects.count()

    # Prepare context data
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users': new_users,
        'total_articles': total_articles,
        'published_articles': published_articles,
        'pending_articles': pending_articles,
        'total_comments': total_comments,
        'total_views': total_views,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)

@login_required
def approve_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    article.status = "published"
    article.save()
    Notification.objects.create(
        user=article.author,
        title="Article Approved",
        message=f"Your article '{article.title}' has been approved and published.",
        is_read=False
    )
    messages.success(request, 'Article approved successfully.')
    return redirect('admin_dashboard')

@login_required
def reject_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    article.delete()  # Or mark it as rejected
    # Notify the user about the rejection
    Notification.objects.create(
        user=article.author,
        title="Article Rejected",
        message=f"Your article '{article.title}' has been rejected.",
        is_read=False
    )
    messages.success(request, 'Article rejected successfully.')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        description = request.POST.get('description', '')

        if not name:
            messages.error(request, 'Category name is required.')
            return redirect('add_category')

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'A category with this name already exists.')
            return redirect('add_category')

        try:
            category = Category.objects.create(name=name, description=description)
            messages.success(request, 'Category added successfully!')
            return redirect('admin_content')  # Redirect to the content moderation page
        except Exception as e:
            messages.error(request, 'An error occurred while adding the category. Please try again.')
            return redirect('add_category')

    return render(request, 'admin/category_add.html')  # Render the form template


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_category(request, category_id):
    logger.info(f"Editing category with ID: {category_id}")

    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        description = request.POST.get('description', '')

        if not name:
            messages.error(request, 'Category name is required.')
            logger.error('Category name is missing.')
            return JsonResponse({'success': False, 'error': 'Category name is required.'}, status=400)

        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Category updated successfully!')
            logger.info(f'Category "{name}" updated successfully.')
            return JsonResponse({'success': True, 'message': 'Category updated successfully!'})
        except Exception as e:
            messages.error(request, 'An error occurred while updating the category. Please try again.')
            logger.error(f'Error updating category: {e}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return render(request, 'admin/category_edit.html', {'category': category})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        category.delete()  # Delete the category
        messages.success(request, 'Category deleted successfully.')
    except Http404:
        messages.error(request, 'Category not found.')
    return redirect('admin_content')  # Redirect to the content moderation page after deletion

def view_articles(request):
    articles = Articles.objects.all().order_by('-created_at')
    
    # Ensure all articles have slugs (optional, might be better in save method)
    for article in articles:
        if not article.slug:
            article.slug = slugify(article.title)
            article.save()
    
    categories = Category.objects.all() # Keep categories if needed by view_article.html
    context = {
        'articles': articles,
        'categories': categories,
        'year': timezone.now().year # Add year if needed by the template
    }
    return render(request, 'view_article.html', context) # Changed template name

@login_required
@subscription_required(required_plan_names=['Premium', 'Pro'])
def article_detail(request, article_id):
    article = Article.objects.get(id=article_id)
    
    # Start tracking reading session
    session = ReadingSession.objects.create(
        user=request.user,
        article=article,
        start_time=timezone.now()
    )
    
    if request.method == 'POST':
        # Update reading session when user leaves the article
        session.end_time = timezone.now()
        session.scroll_depth = float(request.POST.get('scroll_depth', 0))
        session.time_spent = (session.end_time - session.start_time).total_seconds()
        session.save()
        
        # Update user reading profile
        profile, created = UserReadingProfile.objects.get_or_create(user=request.user)
        return render(request, 'thanks.html')
    
    return render(request, 'article_detail.html', {'article': article, 'session_id': session.id})

def get_recommendations(request):
    articles = Article.objects.all()
    profile = UserReadingProfile.objects.get(user=request.user)
    sessions = ReadingSession.objects.filter(user=request.user)
    
    recommendations = recommender.recommend(
        request.user, 
        articles, 
        profile, 
        sessions
    )
    
    return render(request, 'recommendations.html', {'recommendations': recommendations})
def validate_registration_data(username, email, password, confirm_password, first_name, last_name):
    """Validate user registration data."""
    if not first_name.isalpha() or not last_name.isalpha():
        raise ValidationError('First name and last name should only contain alphabets.')

    if password != confirm_password:
        raise ValidationError('Passwords do not match.')

    if User.objects.filter(username=username).exists():
        raise ValidationError('Username already exists.')

    if User.objects.filter(email=email).exists():
        raise ValidationError('Email already exists.')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_verify_user(request, user_id):
    # Logic for verifying a user
    user = User.objects.get(id=user_id)
    user.is_verified = True
    user.save()
    return redirect('admin_user_management')  # Redirect to the user management page

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_get_user_details(request, user_id):
    user = User.objects.get(id=user_id)
    # Logic to retrieve user details
    return JsonResponse({
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        # Add other fields as necessary
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True, 'message': 'All notifications marked as read.'})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def search_articles(request):
    query = request.GET.get('query', '').strip()
    articles = []
    
    if query:
        articles = Articles.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(category__name__icontains=query) | 
            Q(author__username__icontains=query)
        ).filter(status='published').distinct()
        
        # Log the search if user is authenticated
        if request.user.is_authenticated:
            UserSearchHistory.objects.create(
                user=request.user,
                search_term=query
            )
    
    context = {
        'articles': articles,
        'query': query,
        'total_results': len(articles)
    }
    
    return render(request, 'search_results.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def test_notification(request):
            Notification.objects.create(
            user=request.user,
            title="Test Notification",
        message="This is a test notification.",
        notification_type='test',
            is_read=False
        )
            return JsonResponse({'success': True, 'message': 'Test notification sent.'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        # Validate fields
        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return redirect('create_announcement')

        Announcement.objects.create(title=title, message=message)
        messages.success(request, 'Announcement created successfully!')
        return redirect('admin_dashboard')

    return render(request, 'admin/create_announcement.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def test_announcement(request):
    demo_announcement = {
        'title': 'Demo Announcement',
        'message': 'This is a preview of a demo announcement.'
    }
    return render(request, 'admin/test_announcement.html', {'announcement': demo_announcement})

@login_required
def generate_summary(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    summary = simple_summarize(article.content)  # Use the simple_summarize function defined earlier
    return JsonResponse({'summary': summary})

@login_required
def add_article(request):
    title = None  # Default value
    content = None # Default value
    description = None # Default value
    category_id = None # Default value
    if request.method == 'POST':
            title = request.POST.get('title')
            content = request.POST.get('content')
            description = request.POST.get('description', '') # Assuming description might be optional or handled differently
            category_id = request.POST.get('category')
            image = request.FILES.get('image') # Get uploaded image
            pdf_file = request.FILES.get('pdf_file') # Get uploaded PDF
            action = request.POST.get('action') # Check if user clicked 'Publish' or 'Save Draft'

        # Validate fields
    if not title or not content or not category_id:
            messages.error(request, 'Title, content, and category are required.')
            # Repopulate context for rendering the form again
            categories = Category.objects.all()
            return render(request, 'write_article.html', {
                'categories': categories, 
                'title': title, 
                'content': content,
                'description': description,
                'selected_category': category_id
            })

    category = get_object_or_404(Category, id=category_id)

        # Determine status based on action
    article_status = 'published' if action == 'publish' else 'draft'

        # Create the article
    try:
            article = Articles.objects.create(
                title=title,
                content=content,
                description=description, # Add description
                category=category,
                author=request.user, # Set the author
                status=article_status, # Set the status
                image=image, # Add image
                pdf_file=pdf_file # Add PDF file
            )
            if article_status == 'published':
                messages.success(request, 'Article published successfully!')
                # Redirect to the article detail page after publishing
                return redirect(article.get_absolute_url()) 
            else:
                messages.success(request, 'Article saved as draft successfully!')
                # Redirect to drafts page after saving draft
                return redirect('user_drafts') 
    except Exception as e:
            messages.error(request, f'Error creating article: {e}')
             # Repopulate context
    categories = Category.objects.all()
    return render(request, 'write_article.html', {
                'categories': categories, 
                'title': title, 
                'content': content,
                'description': description,
                'selected_category': category_id
            })

    # This part is for GET requests or if POST fails validation before the try block
    categories = Category.objects.all()
    return render(request, 'write_article.html', {'categories': categories})

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id, author=request.user) # Ensure user owns the article
    
    if request.method == 'POST':
        action = request.POST.get('action') # Check action: publish or save_draft
        
        article.title = request.POST.get('title', article.title)
        article.content = request.POST.get('content', article.content)
        article.description = request.POST.get('description', article.description)
        category_id = request.POST.get('category')
        if category_id: # Check if category was actually selected
             article.category = get_object_or_404(Category, id=category_id)
    
        # Handle image update
        if 'image' in request.FILES:
            article.image = request.FILES['image']
        
        # Handle PDF update
        if 'pdf_file' in request.FILES:
            article.pdf_file = request.FILES['pdf_file']
        elif 'remove_pdf' in request.POST: # Add a way to remove PDF if needed
             article.pdf_file = None
        
        # Update status based on action
        if action == 'publish':
            article.status = 'published'
        elif action == 'save_draft': # Or just let it remain draft if already draft
            article.status = 'draft'
             
        # Regenerate slug if title changed (important for published articles)
        # Use article._state.fields_cache to check if the field was loaded in this request cycle
        # or compare original value if available
        # Simplified check: assume title might change
        if article.status == 'published':
            new_slug = slugify(article.title)
            if article.slug != new_slug:
                 article.slug = new_slug
                 # Add logic to handle potential slug conflicts if necessary

        try:
            article.save()
            if article.status == 'published':
                messages.success(request, 'Article updated and published successfully!')
                return redirect(article.get_absolute_url())
            else:
                messages.success(request, 'Draft updated successfully!')
                return redirect('user_drafts')
        except Exception as e:
            messages.error(request, f'Error updating article: {e}')

    categories = Category.objects.all()
    # Use a specific template for editing, perhaps different from write_article if needed
    return render(request, 'write_article.html', {'article': article, 'categories': categories, 'is_editing': True})

@login_required
def delete_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    article.delete()  # Soft delete or mark as inactive
    messages.success(request, 'Article deleted successfully.')
    return redirect('article_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def article_dashboard(request):
    articles = Articles.objects.all()  # Fetch all articles
    # Implement filtering and pagination logic here
    return render(request, 'admin/article_dashboard.html', {'articles': articles})

@login_required
def user_drafts(request):
    drafts = Articles.objects.filter(author=request.user, status='draft').order_by('-created_at')
    return render(request, 'drafts.html', {'drafts': drafts})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def analytics_dashboard(request):
    # Gather analytics data
    return render(request, 'admin/analytics_dashboard.html', {})

# Basic profanity filter (you can expand this)
PROFANITY_LIST = ['badword1', 'badword2']  # Add your profanity words here

def contains_profanity(text):
    """Check if the text contains any profanity."""
    return any(bad_word in text.lower() for bad_word in PROFANITY_LIST)

@login_required
def post_comment(request, article_id):
    """Authenticated users can post a comment to a specific article."""
    article = get_object_or_404(Articles, id=article_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text', '').strip()

        # Validate length and profanity
        if len(comment_text) < 1 or len(comment_text) > 500:
            return JsonResponse({'success': False, 'error': 'Comment must be between 1 and 500 characters.'}, status=400)
        if contains_profanity(comment_text):
            return JsonResponse({'success': False, 'error': 'Your comment contains inappropriate language.'}, status=400)

        comment = Comment.objects.create(user=request.user, article=article, body=comment_text)
        # comment.save() is called implicitly by create()

        # Optionally, create a notification for the article author
        if article.author != request.user: # Don't notify user for their own comment
            Notification.objects.create(
                user=article.author,
                title='New Comment',
                message=f'{request.user.username} commented on your article "{article.title}".',
                link=f'/article/{article.id}/', # Consider using reverse()
                is_read=False,
                created_at=timezone.now()
            )
        return JsonResponse({'success': True, 'comment': comment.body, 'username': request.user.username, 'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')})
    
    # If not POST, return error or perhaps redirect/render differently
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def edit_comment(request, comment_id):
    """Allow users to edit their own comment."""
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.user:
        return JsonResponse({'success': False, 'error': 'You do not have permission to edit this comment.'}, status=403)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'comment_text': comment.body})

    if request.method == 'POST':
        new_comment_text = request.POST.get('comment_text', '').strip()

        # Validate length and profanity
        if len(new_comment_text) < 1 or len(new_comment_text) > 500:
            return JsonResponse({'success': False, 'error': 'Comment must be between 1 and 500 characters.'}, status=400)
        if contains_profanity(new_comment_text):
            return JsonResponse({'success': False, 'error': 'Your comment contains inappropriate language.'}, status=400)

        comment.body = new_comment_text
        comment.save()
        return JsonResponse({'success': True, 'comment': comment.body})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def delete_comment(request, comment_id):
    """Authenticated users can delete their own comments."""
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'You do not have permission to delete this comment.'}, status=403)

        comment.delete()
    return JsonResponse({'success': True, 'message': 'Comment deleted successfully.'})

@login_required
def rate_article(request, article_id):
    """View that shows a modal or rating form to the user."""
    article = get_object_or_404(Articles, id=article_id)
    current_rating = Rating.objects.filter(user=request.user, article=article).first()
    return render(request, 'rate_article.html', {'article': article, 'current_rating': current_rating})

@login_required
def submit_rating(request):
    """Accept POST via AJAX: { article_id, rating_value }."""
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        rating_value = request.POST.get('rating_value')

        # Validate input
        if not rating_value.isdigit() or not (1 <= int(rating_value) <= 5):
            return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5.'}, status=400)

        article = get_object_or_404(Articles, id=article_id)
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'value': rating_value, 'rated_at': timezone.now()}
        )

        # Calculate new average rating
        average_rating = article.ratings.aggregate(Avg('value'))['value__avg'] or 0
        return JsonResponse({'success': True, 'average_rating': average_rating, 'message': 'Rating submitted successfully.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def notifications_view(request):
    """Dashboard view showing all notifications for the user."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def get_notifications(request):
    """Returns a list of latest unread notifications via JSON."""
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    notification_data = [{
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': n.is_read
    } for n in notifications]
    
    return JsonResponse({'success': True, 'notifications': notification_data})

@login_required
def mark_notification_read(request, notification_id):
    """Marks a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True, 'message': 'Notification marked as read.'})

@login_required
def recommendations_view(request):
    try:
        recommendations = Articles.objects.filter(status='published').order_by('-created_at')[:10]

        return render(request, 'recommendations.html', {
            'recommendations': recommendations
        })
    except Exception as e:
        return render(request, 'recommendations.html', {
            'error_message': str(e)
        })
@login_required
def subscription_view(request):
    success = request.GET.get('payment') == 'success'
    error = request.GET.get('payment') in ['failed', 'error']
    
    if success:
        messages.success(request, 'Payment successful! Your subscription is now active.')
    elif error:
        messages.error(request, 'Payment processing failed. Please contact support.')

    """Displays subscription plans and the user's current plan."""
    try:
        # Get or create default plans if they don't exist
        free_plan, _ = Plan.objects.get_or_create(
            name='Free',
            defaults={
                'description': 'Basic free plan',
                'price': 0,
                'duration_days': 0,
                'features': {
                    'read_articles': True,
                    'comment': True,
                    'ad_free': False,
                    'exclusive_content': False
                }
            }
        )
        
        monthly_plan, _ = Plan.objects.get_or_create(
            name='Premium',
            defaults={
                'description': 'Premium monthly plan',
                'price': 100,
                'duration_days': 30,
                'features': {
                    'read_articles': True,
                    'comment': True,
                    'ad_free': True,
                    'exclusive_content': True
                }
            }
        )
        
        six_month_plan, _ = Plan.objects.get_or_create(
            name='Premium 6 Months',
            defaults={
                'description': 'Premium 6 month plan',
                'price': 600,
                'duration_days': 180,
                'features': {
                    'read_articles': True,
                    'comment': True,
                    'ad_free': True,
                    'exclusive_content': True
                }
            }
        )
        
        # Get user's current active plan
        try:
            user_plan = UserPlan.objects.get(user=request.user, is_active=True)
        except UserPlan.DoesNotExist:
            user_plan = None
        
        # Get payment history
        payments = Transaction.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'free_plan': free_plan,
            'monthly_plan': monthly_plan,
            'six_month_plan': six_month_plan,
            'user_plan': user_plan,
            'payments': payments,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
        }
        return render(request, 'subscriptions.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading subscription page: {str(e)}')
        return redirect('home')

@csrf_exempt
@login_required
def create_order(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        order_data = {
            'amount': plan.price_in_paise,
            'currency': 'INR',
            'receipt': f'order_{plan_id}_{request.user.id}',
            'notes': {
                'plan_id': plan.id,
                'user_id': request.user.id
            }
        }
        order = client.order.create(data=order_data)
        
        Subscription.objects.create(
            user=request.user,
            plan=plan,
            razorpay_order_id=order['id'],
            active=False
        )
        
        return JsonResponse({
        'success': True,
        'key': RAZORPAY_KEY_ID,
        'amount': plan.price * 100,
        'currency': 'INR',
        'order_id': razorpay_order_id
    })
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@login_required
def verify_payment(request):
    if request.method == "POST":
        logger.info("Payment verification started")
        try:
            # Extract payment details
            payment_id = request.POST.get('razorpay_payment_id', '').strip()
            order_id = request.POST.get('razorpay_order_id', '').strip()
            signature = request.POST.get('razorpay_signature', '').strip()
            
            logger.debug(f"Received payment details - Payment ID: {payment_id}, Order ID: {order_id}")

            # Validate input parameters
            if not all([payment_id, order_id, signature]):
                logger.error("Missing payment parameters in request")
                return JsonResponse({
                    'success': False,
                    'error': 'Missing payment details. Please contact support.'
                }, status=400)

            # Retrieve subscription and plan
            try:
                subscription = Subscription.objects.select_related('plan').get(
                    razorpay_order_id=order_id,
                    user=request.user
                )
                plan = subscription.plan
                logger.debug(f"Found subscription: {subscription.id} for plan: {plan.id}")
            except Subscription.DoesNotExist:
                logger.error(f"Subscription not found for order ID: {order_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid subscription order. Please contact support.'
                }, status=404)

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify payment signature
            try:
                logger.debug("Attempting signature verification")
                client.utility.verify_payment_signature({
                    'razorpay_payment_id': payment_id,
                    'razorpay_order_id': order_id,
                    'razorpay_signature': signature
                })
                logger.info("Signature verification successful")
            except razorpay.errors.SignatureVerificationError as e:
                logger.error(f"Signature verification failed: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Payment verification failed. Please contact support.'
                }, status=400)

            # Verify payment amount
            try:
                logger.debug("Fetching payment details from Razorpay")
                payment = client.payment.fetch(payment_id)
                if payment['amount'] != plan.price_in_paise:
                    logger.error(f"Amount mismatch: Expected {plan.price_in_paise}, Got {payment['amount']}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Payment amount mismatch. Please contact support.'
                    }, status=400)
                logger.info("Payment amount verified successfully")
            except Exception as e:
                logger.error(f"Payment verification failed: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Payment verification failed. Please try again.'
                }, status=500)
            if payment_valid:
            # Save to database
                Subscription.objects.create(
            user=request.user,
            plan=plan,
            payment_id=payment_id,
            status='Active'
        )
            return JsonResponse({
            'success': True,
            'redirect_url': reverse('subscriptions')
        })
            return JsonResponse({'success': False})
            # Process subscription activation
            with transaction.atomic():
                logger.debug("Starting database transaction")
                
                # Update subscription
                subscription.razorpay_payment_id = payment_id
                subscription.razorpay_signature = signature
                subscription.active = True
                subscription.save()
                logger.info(f"Subscription {subscription.id} updated")

                # Deactivate existing plans
                deactivated = UserPlan.objects.filter(
                    user=request.user,
                    is_active=True
                ).update(is_active=False)
                logger.info(f"Deactivated {deactivated} existing plans")

                # Create new user plan
                end_date = timezone.now() + timedelta(days=plan.duration_days)
                new_plan = UserPlan.objects.create(
                    user=request.user,
                    plan=plan,
                    is_active=True,
                    start_date=timezone.now(),
                    end_date=end_date,
                    auto_renew=False
                )
                logger.info(f"Created new user plan: {new_plan.id}")

                # Create transaction record
                transaction_record = Transaction.objects.create(
                    user=request.user,
                    plan=plan,
                    amount=plan.price,
                    payment_method='Razorpay',
                    payment_id=payment_id,
                    status='completed'
                )
                logger.info(f"Created transaction record: {transaction_record.id}")

                # Create notification
                Notification.objects.create(
                    user=request.user,
                    title='Subscription Activated',
                    message=f'Your {plan.name} plan is active until {end_date.strftime("%B %d, %Y")}',
                    notification_type='subscription',
                    related_link=reverse('subscription')
                )
                logger.info("Created notification")

                logger.info("Subscription activated successfully")
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('subscription') + '?payment=success'
                })

        except Exception as e:
            logger.critical(f"Critical error in verify_payment: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred. Our team has been notified.',
                'redirect_url': reverse('subscription') + '?payment=failed',
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)
@login_required
def payment_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    context = {
        'plan': plan,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'now': timezone.now()  # Add this line
    }
    return render(request, 'payment.html', context)
@login_required
def update_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect!')
            return redirect('profile')
            
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('profile')
            
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters!')
            return redirect('profile')

        user.set_password(new_password)
        user.save()
        
        # Re-authenticate user after password change
        update_session_auth_hash(request, user)
        messages.success(request, 'Password updated successfully!')
        return redirect('profile')
        
    return redirect('profile')
# Add these functions to your views.py file



@login_required
def subscription_page(request):
    """View for subscription page with success message handling"""
    success = request.GET.get('success', False)
    message = request.GET.get('message', '')
    
    # Check if user has active subscription
    active_subscription = UserPlan.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()
    
    # Get available plans
    plans = Plan.objects.all()
    
    context = {
        'plans': plans,
        'active_subscription': active_subscription,
        'success': success,
        'message': message
    }
    
    return render(request, 'subscriptions.html', context)

@login_required
def payment_page(request):
    """View for payment page with plan details"""
    plan_id = request.GET.get('plan_id')
    
    if not plan_id:
        return redirect('subscription_page')
    
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return redirect('subscription_page')
    
    context = {
        'plan': plan
    }
    
    return render(request, 'payment.html', context)

@csrf_exempt
@login_required
def update_subscription(request):
    """API endpoint to update subscription after successful payment"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    plan_id = request.POST.get('plan_id')
    payment_id = request.POST.get('payment_id')
    
    if not plan_id or not payment_id:
        return JsonResponse({'success': False, 'message': 'Missing required parameters'})
    
    try:
        # Get the plan
        plan = Plan.objects.get(id=plan_id)
        
        # Create subscription record
        subscription = Subscription(
            user=request.user,
            plan=plan,
            razorpay_payment_id=payment_id,
            active=True
        )
        subscription.save()
        
        # Calculate end date based on plan duration
        end_date = timezone.now() + timedelta(days=plan.duration_days)
        
        # Check if user already has an active plan
        existing_plan = UserPlan.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if existing_plan:
            # Update existing plan
            existing_plan.plan = plan
            existing_plan.start_date = timezone.now()
            existing_plan.end_date = end_date
            existing_plan.is_active = True
            existing_plan.stripe_subscription_id = payment_id  # Using Razorpay ID here
            existing_plan.save()
        else:
            # Create new user plan
            user_plan = UserPlan(
                user=request.user,
                plan=plan,
                start_date=timezone.now(),
                end_date=end_date,
                is_active=True,
                stripe_subscription_id=payment_id  # Using Razorpay ID here
            )
            user_plan.save()
        
        return JsonResponse({'success': True})
    
    except Plan.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Plan not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_POST
def start_reading_session(request):
    article_id = request.POST.get('article_id')
    if not article_id or not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    article = get_object_or_404(Articles, id=article_id)
    session = ReadingSession.objects.create(
        user=request.user,
        article=article,
        start_time=timezone.now()
    )
    return JsonResponse({'success': True, 'session_id': session.id})

@csrf_exempt
@require_POST
def end_reading_session(request):
    session_id = request.POST.get('session_id')
    scroll_depth = float(request.POST.get('scroll_depth', 0))
    
    if not session_id or not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    session = get_object_or_404(ReadingSession, id=session_id, user=request.user)
    session.end_time = timezone.now()
    session.scroll_depth = scroll_depth
    session.save()
    
    # Update user's reading profile
    if session.words_per_minute:
        profile, created = UserReadingProfile.objects.get_or_create(user=request.user)
        profile.update_reading_speed(session.words_per_minute)
    
    return JsonResponse({
        'success': True,
        'wpm': session.words_per_minute,
        'time_spent': session.time_spent
    })

def home_view(request):
    # Only fetch published articles
    articles = Articles.objects.filter(status='published').order_by('-created_at')[:6]
    
    recommendations = []
    if request.user.is_authenticated:
        try:
            profile = UserReadingProfile.objects.get(user=request.user)
            sessions = ReadingSession.objects.filter(user=request.user)
            recommender = ContentRecommender()
            recommendations = recommender.recommend(
                request.user, 
                Articles.objects.all(), 
                profile, 
                sessions,
                top_n=3
            )
        except UserReadingProfile.DoesNotExist:
            pass
    
    context = {
        'articles': articles,
        'recommendations': recommendations,
    }
    return render(request, 'home.html', context)
@login_required
def update_preferences(request):
    """Updates user's content preferences."""
    if request.method == 'POST':
        try:
            # Get selected categories
            category_ids = request.POST.getlist('categories')
            categories = Category.objects.filter(id__in=category_ids)
            
            # Get or create user preferences
            preferences, created = UserPreferences.objects.get_or_create(user=request.user)
            
            # Update preferred categories
            preferences.preferred_categories.set(categories)
            
            messages.success(request, 'Your preferences have been updated successfully!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Error updating preferences: {str(e)}')
            return redirect('profile')
    
    return redirect('profile')

@login_required
def payment_success(request):
    """Handle successful payment."""
    messages.success(request, 'Payment successful! Your subscription has been activated.')
    return redirect('subscription')

@login_required
def payment_cancel(request):
    """Handle cancelled payment."""
    messages.warning(request, 'Payment was cancelled. Your subscription has not been activated.')
    return redirect('subscription')

@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhook events."""
    if request.method == "POST":
        try:
            # Get webhook data
            webhook_data = json.loads(request.body)
            
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Verify webhook signature
            webhook_signature = request.headers.get('X-Razorpay-Signature')
            client.utility.verify_webhook_signature(request.body.decode(), webhook_signature, settings.RAZORPAY_WEBHOOK_SECRET)
            
            # Handle different webhook events
            if webhook_data['event'] == 'payment.captured':
                payment_id = webhook_data['payload']['payment']['entity']['id']
                order_id = webhook_data['payload']['payment']['entity']['order_id']
                
                try:
                    subscription = Subscription.objects.get(razorpay_order_id=order_id)
                    
                    # Update subscription status
                    subscription.razorpay_payment_id = payment_id
                    subscription.active = True
                    subscription.save()
                    
                    # Create or update user plan
                    UserPlan.objects.filter(user=subscription.user, is_active=True).update(is_active=False)
                    UserPlan.objects.create(
                        user=subscription.user,
                        plan=subscription.plan,
                        is_active=True,
                        end_date=timezone.now() + timedelta(days=subscription.plan.duration_days)
                    )
                    
                    # Create transaction record
                    transaction_record = Transaction.objects.create(
                        user=subscription.user,
                        plan=subscription.plan,
                        amount=subscription.plan.price,
                        payment_method='Razorpay',
                        payment_id=payment_id,
                        status='completed'
                    )
                    
                    # Create notification
                    Notification.objects.create(
                        user=subscription.user,
                        title='Subscription Activated',
                        message=f'Your {subscription.plan.name} plan subscription is now active.',
                        notification_type='subscription'
                    )
                    
                except Subscription.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Subscription not found'}, status=400)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def switch_to_free_plan(request):
    """Switch the user's subscription to the free plan."""
    try:
        free_plan = Plan.objects.get(name='Free')
        user_plan = UserPlan.objects.get(user=request.user, is_active=True)
        user_plan.plan = free_plan
        user_plan.save()
        messages.success(request, 'You have successfully switched to the Free plan.')
    except Plan.DoesNotExist:
        messages.error(request, 'The Free plan does not exist.')
    except UserPlan.DoesNotExist:
        messages.error(request, 'You do not have an active subscription to switch.')
    
    return redirect('subscription')  # Redirect back to the subscription page