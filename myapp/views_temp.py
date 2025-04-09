from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Notification

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
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
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email address.')

    return render(request, 'account/login.html') 