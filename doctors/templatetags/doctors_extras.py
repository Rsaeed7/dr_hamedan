from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value 