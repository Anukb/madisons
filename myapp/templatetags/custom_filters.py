from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value 

@register.filter
def divide(value, arg):
    """Divide value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
