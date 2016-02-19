import os
import re

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

from clients.models import Client

register = template.Library()


@register.inclusion_tag("healer_item.html")
def show_healer(user):
	return {"user": user}


@register.simple_tag
def rating_star_css_class(rating):
	rating = float(rating)
	if not rating:
		return 'icon_star_empty'

	return 'icon_star_%s' % str(int(rating/0.5+0.5)*0.5).replace('.', '_')


@register.simple_tag
def featured_image(user):
	return '<img src="%s%s.png" alt="%s"/>' % (
		settings.FEATURED_PROVIDERS_URL, user.username, user.get_full_name())


@register.simple_tag
def clear_search_url(request):
	getvars = request.GET.copy()
	if "search" in getvars:
		del getvars["search"]
	if len(getvars.keys()) > 0:
		return "%s?%s" % (request.path, getvars.urlencode())
	else:
		return request.path


@register.inclusion_tag('jquery_js_import.html')
def jquery_js_import():
	return {
		"RUNNING_LOCAL": settings.RUNNING_LOCAL,
		"STATIC_URL": settings.STATIC_URL
	}


@register.inclusion_tag('jquery_ui_js_import.html')
def jquery_ui_js_import():
	return {
		'RUNNING_LOCAL': settings.RUNNING_LOCAL,
		'STATIC_URL': settings.STATIC_URL
	}


@register.inclusion_tag('jquery_ui_css_import.html')
def jquery_ui_css_import():
	return {
		'RUNNING_LOCAL': settings.RUNNING_LOCAL,
		'STATIC_URL': settings.STATIC_URL
	}


version_cache = {}
rx = re.compile(r"^(.*)\.(.*?)$")


@register.simple_tag
def version(path_string):
	try:
		if settings.SERVE_MEDIA:
			return settings.STATIC_URL + path_string
		if path_string in version_cache:
			mtime = version_cache[path_string]
		else:
			mtime = os.path.getmtime(os.path.join(settings.STATIC_ROOT, path_string))
			version_cache[path_string] = mtime

		return settings.STATIC_URL + rx.sub(r"\1.%d.\2" % mtime, path_string)
	except:
		return path_string


@register.filter
def hs_truncatewords_html(value, arg):
	"""
	Truncate HTML after a certain number of words.

	Argument: Number of words to truncate after.

	Newlines in the HTML are preserved.
	"""
	from healers.utils import truncate_html_words
	try:
		length = int(arg)
	except ValueError:  # invalid literal for int()
		return value  # Fail silently.
	return truncate_html_words(value, length)
hs_truncatewords_html.is_safe = True
hs_truncatewords_html = template.defaultfilters.stringfilter(hs_truncatewords_html)


@register.filter
def client_gallery(user):
	"""Return gallery for the user."""
	client = Client.objects.get(user=user)
	return client.gallery_set.filter(hidden=False).order_by('order')


@register.simple_tag
def invalid_tlength_error(user, length):
	if user.client.healer.has_enabled_stripe_connect() and not length.is_valid_cost():
		return '<div class="length_cost_error">- Warning: This option is not available for Online Payment</div>'
	return ''


@register.simple_tag
def add_edit_provider_treatments(center_user, provider_user):
	has_center_treatments = provider_user.client.healer.has_center_treatments(center_user)
	link = reverse('treatment_types', args=[provider_user.username])
	if has_center_treatments:
		name = 'Edit'
		additional_class = ''
	else:
		name = 'Add'
		additional_class = 'lightred'
	return '<a class="highlight_button {}" href="{}">{} Treatments &raquo;</a>'.format(additional_class, link, name)
