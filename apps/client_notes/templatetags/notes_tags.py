from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def marker_html_element(marker, is_phonegap):
	if marker.image is None:
		return '<div class="marker_color" style="background-color: %s"></div>' % marker.color
	else:
		static_url = settings.STATIC_URL
		if is_phonegap:
			static_url = static_url[1:]
		return '<img class="marker_image" src="%shealersource/img/notes/markers/%s.png" alt="%s">' % (
			static_url, marker.image, marker.name)
