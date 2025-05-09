# In your context_processors.py
from django.utils import timezone

def current_datetime(request):
    return {
        'now': timezone.now()
    }