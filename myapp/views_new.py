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

@login_required
def get_notifications(request):
    try:
        # Get all notifications for the user
        all_notifications = Notification.objects.filter(user=request.user)
        # Count unread notifications
        unread_count = all_notifications.filter(is_read=False).count()
        # Get the 10 most recent notifications
        recent_notifications = all_notifications.order_by('-created_at')[:10]
        
        data = {
            "notifications": [
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read
                }
                for notification in recent_notifications
            ],
            "unread_count": unread_count
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500) 