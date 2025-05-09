from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserPlan
from django.utils import timezone

def subscription_required(required_plan_names=None):
    """
    Decorator for views that requires the user to have an active subscription.
    Optionally checks if the user's plan name is in required_plan_names.
    Assumes a Free plan has price 0 or specific characteristics if needed.
    """
    if required_plan_names is None:
        required_plan_names = [] # Default: any active non-free plan

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this content.")
                return redirect('login') # Or your login URL

            try:
                user_plan = UserPlan.objects.get(user=request.user, is_active=True)
                if not user_plan.check_is_active(): # Double-check expiry
                    raise UserPlan.DoesNotExist

                # If specific plan names are required, check if the user's plan is one of them
                if required_plan_names:
                    if user_plan.plan.name not in required_plan_names:
                        messages.error(request, f"This content requires a {', '.join(required_plan_names)} subscription.")
                        return redirect('subscription') # Redirect to subscription page
                # If no specific plans required, any active plan (implicitly non-free if needed) is okay
                # Add logic here if you need to differentiate free vs paid, e.g.:
                # elif plan.price == 0:
                #    messages.error(request, "This content requires a paid subscription.")
                #    return redirect('subscription') 
                    
            except UserPlan.DoesNotExist:
                messages.error(request, "An active subscription is required to access this content.")
                return redirect('subscription') # Redirect to subscription page

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 