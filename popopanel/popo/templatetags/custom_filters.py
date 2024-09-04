import os
from django import template

register = template.Library()

@register.filter
def isdir(value, base_path):
    full_path = os.path.join(base_path, value)
    return os.path.isdir(full_path)

