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
from .models import Plan, UserPlan, Transaction
from django.urls import reverse
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
        # Update User fields
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')

        # Update Profile fields
        profile.user_type = request.POST.get('user_type')
        profile.bio = request.POST.get('bio')

        # Save the updates
        request.user.save()
        profile.save()

        messages.success(request, 'Your profile has been updated!')
        return redirect('profile')  # Redirect to the profile page

    return render(request, 'account/edit_profile.html', {'profile': profile})

@login_required
def profile_view(request):
    user_preferences, created = UserPreferences.objects.get_or_create(user=request.user)

    # Ensure the profile exists
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('name').split()[0]
        user.last_name = request.POST.get('name').split()[1]
        user.bio = request.POST.get('bio')

        # Handle profile picture upload
        if request.FILES.get('profile_pic'):
            profile.profile_pic = request.FILES['profile_pic']  # Save to Profile model

        # Handle interests
        interests = request.POST.getlist('interests')
        user_preferences.preferred_categories.set(interests)

        user.save()
        user_preferences.save()
        profile.save()  # Save the profile
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {
        'user': request.user,
        'categories': Category.objects.all(),
        'user_preferences': user_preferences,
        'profile': profile  # Pass the profile to the template
    })

def home_view(request):
    # Only fetch published articles
    articles = Articles.objects.filter(status='published')
    return render(request, 'home.html', {'articles': articles})

def welcome_notification(user):
    """Create a welcome notification for new users"""
    return Notification.objects.create(
        user=user,
        title="Welcome to Madison!",
        message="Welcome to Madison! We're excited to have you join our community. Start exploring articles or write your own to share your knowledge.",
        notification_type='welcome',
        is_read=False
    )

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
        # Create welcome notification
        Notification.objects.create(
            user=user,
            title="Welcome to Madison!",
            message="Thank you for joining Madison. Start exploring articles and connecting with other readers!",
            notification_type='welcome'
        )
        return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

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
    context = {
        # User Statistics
        'total_users': User.objects.exclude(is_superuser=True).count(),
        'active_users': User.objects.exclude(is_superuser=True).filter(is_active=True).count(),
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
@login_required
def reading_history_view(request):
    # Get all reading history for the logged-in user, newest first
    history_entries = ReadingHistory.objects.select_related('article').filter(user=request.user).order_by('-timestamp')

    context = {
        'reading_history': history_entries,
    }

    return render(request, 'account/reading_history.html', context)
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

logger = logging.getLogger(__name__)

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
            # Update the category
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
    # Only show published articles
    articles = Articles.objects.filter(status='published')
    return render(request, 'view_article.html', {'articles': articles})

@login_required
def article_detail(request, article_id, slug):
    article = get_object_or_404(Articles, id=article_id, slug=slug)
    
    if request.user.is_authenticated:
        # Record that the user has viewed this article
        UserViewedArticle.objects.get_or_create(user=request.user, article=article)
        ReadingHistory.objects.get_or_create(user=request.user, article=article)
    
    return render(request, 'article_detail.html', {'article': article})

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
    query = request.GET.get('query', '')
    articles = Articles.objects.filter(Q(title__icontains=query) | Q(category__name__icontains=query) | Q(author__username__icontains=query)).distinct()
    return render(request, 'search_results.html', {'articles': articles})

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
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        # Validate fields
        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return redirect('add_article')
        
            category = get_object_or_404(Category, id=category_id)
        article = Articles.objects.create(title=title, content=content, category=category)
        messages.success(request, 'Article created successfully!')
        return redirect('article_dashboard')

    categories = Category.objects.all()
    return render(request, 'admin/add_article.html', {'categories': categories})

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    
    if request.method == 'POST':
        article.title = request.POST.get('title', article.title)
        article.content = request.POST.get('content', article.content)
        article.category_id = request.POST.get('category', article.category_id)
        article.save()
        messages.success(request, 'Article updated successfully!')
        return redirect('article_dashboard')
    
    categories = Category.objects.all()
    return render(request, 'admin/edit_article.html', {'article': article, 'categories': categories})

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
    return render(request, 'admin/user_drafts.html', {'drafts': drafts})

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
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text', '').strip()

        # Validate length and profanity
        if len(comment_text) < 1 or len(comment_text) > 500:
            return JsonResponse({'success': False, 'error': 'Comment must be between 1 and 500 characters.'}, status=400)
        if contains_profanity(comment_text):
            return JsonResponse({'success': False, 'error': 'Your comment contains inappropriate language.'}, status=400)

        article = get_object_or_404(Articles, id=article_id)
        comment = Comment.objects.create(user=request.user, article=article, body=comment_text)
        comment.save()

        # Optionally, create a notification for the article author
        Notification.objects.create(
            user=article.author,
            title='New Comment',
            message=f'{request.user.username} commented on your article "{article.title}".',
            link=f'/article/{article.id}/',
            is_read=False,
            created_at=timezone.now()
        )

        return JsonResponse({'success': True, 'comment': comment.body, 'username': request.user.username, 'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')})

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
    recommendations = get_recommendations(request.user)  # Assuming you have a function to get recommendations
    return render(request, 'recommendations.html', {'recommendations': recommendations})

@login_required
def subscription_view(request):
    # Logic for displaying subscription options
    plans = Plan.objects.all()  # Assuming you have a Plan model
    return render(request, 'subscription.html', {'plans': plans})