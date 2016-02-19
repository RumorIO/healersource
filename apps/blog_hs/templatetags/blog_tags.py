# -*- coding: utf-8 -*-
import re

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe


register = template.Library()



@register.inclusion_tag("blog/blog_item.html")
def show_blog_post(blog_post):
	return {"blog_post": blog_post}

@register.simple_tag
def post_url(blog_post, view=None):
	if not view:
		view = "blog_post"

	return reverse(view, kwargs={
		"username": blog_post.user.username,
		"year": blog_post.publish_date.year,
		"month": "%02d" % blog_post.publish_date.month,
		"slug_id": blog_post.id
	})

@register.simple_tag
def post_popup_url(blog_post):
	return reverse("blog_post_popup", kwargs={
		"username": blog_post.user.username,
		"year": blog_post.publish_date.year,
		"month": "%02d" % blog_post.publish_date.month,
		"slug_id": blog_post.id
	})
