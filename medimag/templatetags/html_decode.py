import html
from django import template

register = template.Library()

@register.filter
def html_decode(value):
    return html.unescape(value)
