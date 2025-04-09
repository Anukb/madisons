from django import template
from myapp.models import Notification

register = template.Library()

@register.inclusion_tag('notifications/notification_list.html', takes_context=True)
def show_notifications(context):
    request = context['request']
    # Get all notifications for the user
    all_notifications = Notification.objects.filter(user=request.user)
    # Count unread notifications before slicing
    unread_count = all_notifications.filter(is_read=False).count()
    # Get the 5 most recent notifications
    notifications = all_notifications.order_by('-created_at')[:5]
    
    return {
        'notifications': notifications,
        'unread_count': unread_count
    }

@register.simple_tag
def get_user_notifications(user):
    if user.is_authenticated:
        return Notification.objects.filter(user=user).order_by('-created_at')[:5]
    return [] 