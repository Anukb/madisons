from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from .models import Category, Articles, UserSearchHistory, UserViewedArticle, UserInteraction, UserPreferences, Profile, Comment, Rating, Notification, Event, Complaint, UserActivity, AdminLog, Report
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
from django.core.cache import cache
import os
from transformers import pipeline
import csv
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models.functions import TruncDate

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

def create_welcome_notification(user):
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
            if user.check_password(password):
                login(request, user)
                # Create a test notification
                Notification.objects.create(
                    user=user,
                    title="Welcome Back!",
                    message=f"Welcome back to Madison Magazine, {user.username}!",
                    is_read=False
                )
                return redirect('home')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
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
def admin_dashboard(request):
    if not request.user.is_staff:
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
        }
    }
    
    return render(request, 'account/admin_dashboard.html', context)

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
    categories = Category.objects.all().order_by('-created_at')
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    resolved_today = Report.objects.filter(
        status='resolved', 
        updated_at__date=timezone.now().date()
    ).count()
    
    context = {
        'categories': categories,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'resolved_today': resolved_today,
    }
    return render(request, 'admin/content_moderation.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_category(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'Category name is required'
                }, status=400)
                
            category = Category.objects.create(
                name=name,
                description=description
            )
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'created_at': category.created_at.strftime('%b %d, %Y')
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

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
def admin_analytics(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get date range from request or default to last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    date_range = request.GET.get('range', '30')  # Default to 30 days
    
    if date_range == '7':
        start_date = end_date - timedelta(days=7)
    elif date_range == '90':
        start_date = end_date - timedelta(days=90)
    
    context = {
        # User Statistics
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'new_users': User.objects.filter(date_joined__gte=start_date).count(),
        
        # Content Statistics
        'total_articles': Articles.objects.count(),
        'pending_articles': Articles.objects.filter(status='draft').count(),
        'published_articles': Articles.objects.filter(status='published').count(),
        
        # Complaint Statistics
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status='pending').count(),
        'resolved_complaints': Complaint.objects.filter(status='resolved').count(),
        
        # User Growth Data
        'user_growth': User.objects.annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).filter(
            date_joined__range=(start_date, end_date)
        ).order_by('date'),
        
        # Content Distribution
        'content_distribution': {
            'articles': Articles.objects.count(),
            'comments': Comment.objects.count(),
            'complaints': Complaint.objects.count()
        },
        
        # Top Content
        'top_articles': Articles.objects.annotate(
            view_count=Count('userviewedarticle')
        ).order_by('-view_count')[:5],
        
        # Date Range Context
        'start_date': start_date,
        'end_date': end_date,
        'selected_range': date_range
    }
    
    return render(request, 'admin/analytics.html', context)

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
def edit_category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found.'})

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required.'})
            
        # Check if another category with same name exists
        if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
            return JsonResponse({'success': False, 'error': 'A category with this name already exists.'})
            
        try:
            category.name = name
            category.description = description
            category.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def create_article(request):
    if request.method == 'POST':
        try:
            title = request.POST['title']
            description = request.POST['description']
            content = request.POST['content']
            category_id = request.POST['category']
            status = request.POST.get('status', 'draft')  # Default to draft if not provided

            # Get the category object
            category = get_object_or_404(Category, id=category_id)

            # Create the article
            article = Articles.objects.create(
                title=title,
                description=description,
                content=content,
                category=category,
                author=request.user,
                status=status
            )
            return redirect('article_dashboard')
        except Exception as e:
            # Log the error (you can also use Django's logging framework)
            print(f"Error creating article: {str(e)}")
            messages.error(request, 'An error occurred while creating the article. Please try again.')
            return redirect('add_article')  # Redirect back to the article creation page

    return render(request, 'write_article.html')

@login_required
def article_dashboard(request):
    try:
        # Get user's articles
        articles = Articles.objects.filter(author=request.user)
        drafts = articles.filter(status='draft').select_related('category')
        published_articles = articles.filter(status='published').select_related('category')
        
        return render(request, 'article_dashboard.html', {
            'drafts': drafts,
            'published_articles': published_articles
        })
    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        messages.error(request, 'An error occurred while loading your articles. Please try again.')
        return redirect('home')

def view_articles(request):
    # Only show published articles
    articles = Articles.objects.filter(status='published')
    return render(request, 'view_article.html', {'articles': articles})

@login_required
def article_detail(request, article_id):
    article = get_object_or_404(Articles, id=article_id)
    
    if request.user.is_authenticated:
        # Record that the user has viewed this article
        UserViewedArticle.objects.get_or_create(user=request.user, article=article)
    
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

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        try:
            # Call your validation function
            validate_registration_data(username, email, password, confirm_password, first_name, last_name)

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create the corresponding Profile instance
            Profile.objects.create(user=user)

            # Create default UserPreferences instance
            UserPreferences.objects.create(user=user)
            
            # Create welcome notification
            Notification.objects.create(
                user=user,
                title="Welcome to Madison!",
                message="Welcome to Madison! We're excited to have you join our community. Start exploring articles or write your own to share your knowledge.",
                notification_type='welcome',
                is_read=False
            )

            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('register')

    return render(request, 'account/register.html')  # Show empty form on GET

def check_username(request):
    username = request.GET.get('username')
    if username:
        exists = User.objects.filter(username=username).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})

@login_required
def user_drafts(request):
    try:
        # Get all draft articles for the current user
        drafts = Articles.objects.filter(
            author=request.user,
            status='draft'
        ).select_related('category').order_by('-created_at')  # Most recent drafts first
        
        return render(request, 'drafts.html', {
            'drafts': drafts,
        })
    except Exception as e:
        print(f"Error fetching drafts: {str(e)}")  # Log the error
        messages.error(request, 'An error occurred while fetching your drafts. Please try again.')
        return redirect('home')

def content_browsing(request):
    # Only show published articles
    articles = Articles.objects.filter(status='published')
    categories = Category.objects.all()
    return render(request, 'content_browsing.html', {
        'articles': articles,
        'categories': categories
    })

def welcome_notification(request):
    """Create a welcome notification for new users"""
    if request.user.is_authenticated:
        # Create welcome notification
        Notification.objects.create(
            user=request.user,
            title="Welcome to Madison",
            message="Welcome to Madison! We're excited to have you join our community. Start exploring articles and connecting with other readers.",
            notification_type='welcome'
        )
        return JsonResponse({'status': 'success', 'message': 'Welcome notification created'})
    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

@login_required
def admin_verify_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user = User.objects.get(id=user_id)
        profile = user.userprofile
        profile.is_verified = True
        profile.save()

        AdminLog.objects.create(
            admin=request.user,
            action='verify_user',
            target_model='User',
            target_id=user.id,
            details=f"Verified user {user.username}"
        )

        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
def admin_get_user_details(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user = User.objects.get(id=user_id)
        profile = user.userprofile
        recent_activity = UserActivity.objects.filter(user=user).order_by('-timestamp')[:5]

        data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'is_active': user.is_active,
            'is_verified': profile.is_verified,
            'last_active': profile.last_active.strftime('%Y-%m-%d %H:%M:%S'),
            'profile_pic': user.profile.profile_pic.url if hasattr(user, 'profile') else None,
            'recent_activity': [{
                'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'description': activity.description
            } for activity in recent_activity]
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
def admin_delete_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()

        AdminLog.objects.create(
            admin=request.user,
            action='delete_user',
            target_model='User',
            target_id=user_id,
            details=f"Deleted user {username}"
        )

        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
def admin_export_users(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        format = request.POST.get('format', 'csv')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        fields = json.loads(request.POST.get('fields', '{}'))

        # Get users based on date range if provided
        users = User.objects.all()
        if start_date:
            users = users.filter(date_joined__gte=start_date)
        if end_date:
            users = users.filter(date_joined__lte=end_date)

        # Create the response based on the requested format
        if format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
            writer = csv.writer(response)
            
            # Write headers
            headers = []
            if fields.get('id'): headers.append('ID')
            if fields.get('name'): headers.append('Name')
            if fields.get('email'): headers.append('Email')
            if fields.get('join_date'): headers.append('Join Date')
            if fields.get('status'): headers.append('Status')
            writer.writerow(headers)

            # Write data
            for user in users:
                row = []
                if fields.get('id'): row.append(user.id)
                if fields.get('name'): row.append(user.get_full_name())
                if fields.get('email'): row.append(user.email)
                if fields.get('join_date'): row.append(user.date_joined.strftime('%Y-%m-%d'))
                if fields.get('status'): row.append('Active' if user.is_active else 'Inactive')
                writer.writerow(row)

            return response
        else:
            return JsonResponse({'error': 'Unsupported export format'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def admin_complaints(request):
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get query parameters for filtering
    status_filter = request.GET.get('status', '')
    
    # Base queryset with related data
    complaints = Complaint.objects.select_related('user').all().order_by('-created_at')
    
    # Apply filters
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(complaints, 20)  # Show 20 complaints per page
    page = request.GET.get('page')
    try:
        complaints = paginator.page(page)
    except PageNotAnInteger:
        complaints = paginator.page(1)
    except EmptyPage:
        complaints = paginator.page(paginator.num_pages)
    
    context = {
        'complaints': complaints,
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status='pending').count(),
        'resolved_complaints': Complaint.objects.filter(status='resolved').count(),
        'status_filter': status_filter
    }
    
    return render(request, 'admin/complaints.html', context)

