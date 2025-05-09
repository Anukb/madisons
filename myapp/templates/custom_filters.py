from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts arg from value."""
    return value - arg

print("Custom filters loaded")
def divide(value, arg):
    try:
        return (int(value) / int(arg)) * 60  # Convert to minutes
    except (ValueError, ZeroDivisionError):
        return 0