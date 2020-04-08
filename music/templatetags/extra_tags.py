from django import template

register = template.Library()


@register.simple_tag
def get_mod2(val=None):
    return val % 2

