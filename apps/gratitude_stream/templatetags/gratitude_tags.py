from django import template
from django.contrib.contenttypes.models import ContentType

from gratitude_stream.models import PostComment, Like, Report


register = template.Library()


@register.assignment_tag
def get_comments(post):
	post_content_type = ContentType.objects.get(app_label='gratitude_stream', model='post')
	return PostComment.objects.filter(content_type=post_content_type, object_pk=post.pk)


@register.simple_tag
def like_action(posting, user):
	html = ''
	posting_content_type = ContentType.objects.get(app_label='gratitude_stream', model=posting.type())

	if not Like.objects.filter(user=user, posting_content_type=posting_content_type, posting_object_id=posting.pk).exists():
		html = '<a href="javascript:void(0);" class="like action_item">Like</a>'
	return html


@register.simple_tag
def report_action(posting, user):
	html = ''
	posting_content_type = ContentType.objects.get(app_label='gratitude_stream', model=posting.type())
	if not Report.objects.filter(user=user, posting_content_type=posting_content_type, posting_object_id=posting.pk).exists():
		html = '<a href="javascript:void(0);" class="report">Report Spam</a>'
	return html
