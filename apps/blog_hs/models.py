from django.utils.html import strip_tags
from django.template.defaultfilters import truncatewords_html


def description_from_content(post):
	"""
	Returns 100 words of the content field.
	"""
	description = strip_tags(truncatewords_html(post.content, 100))
	return description
