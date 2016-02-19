from django import template
from clients.utils import get_avatar

register = template.Library()


@register.simple_tag
def avatar(user, size, external=False, get_url=False, phonegap=False, no_size=False):
	return get_avatar(user, size, external, get_url, phonegap, no_size)
