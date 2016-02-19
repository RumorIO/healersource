from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from rest_framework.response import Response

from account_hs.authentication import user_authenticated
from account_hs.views import UserAuthenticated
from gratitude_stream.models import (Post, Question, PostComment, Like,
	Report, SpammingUser)


@user_authenticated
def home(request):
	POST_LIMIT = 50
	return render_to_response('gratitude_stream/home.html',
		{
			'question': Question.objects.all()[0],
			'posts': Post.objects.all()[:POST_LIMIT],
			'is_user_blocked': SpammingUser.objects.filter(user=request.user).exists()
		}, context_instance=RequestContext(request))


class GratitudeStreamView(UserAuthenticated):
	def is_allowed_to_post(self):
		return not SpammingUser.objects.filter(user=self.request.user).exists()

	def get_posting_content_type(self, posting_type):
		self.posting_content_type = ContentType.objects.get(app_label='gratitude_stream', model=posting_type)


class PostPost(GratitudeStreamView):
	def post(self, request, question_id, format=None):
		text = request.POST.get('text')
		if self.is_allowed_to_post() and text:
			question = Question.objects.get(pk=question_id)
			post = Post.objects.create(user=request.user, question=question, text=text)
			html = render_to_string('gratitude_stream/posting.html', {'posting': post, 'user': request.user})
			return Response({'html': html})


class Comment(GratitudeStreamView):
	def post(self, request, post_id, format=None):
		comment = request.POST.get('comment')
		if self.is_allowed_to_post() and comment:
			post_content_type = ContentType.objects.get(app_label='gratitude_stream', model='post')
			comment = PostComment.objects.create(user=request.user, comment=comment, content_type=post_content_type, object_pk=post_id)
			html = render_to_string('gratitude_stream/posting.html', {'posting': comment, 'user': request.user})
			return Response({'html': html})


class PostLike(GratitudeStreamView):
	def post(self, request, posting_type, posting_id, format=None):
		self.get_posting_content_type(posting_type)
		like = Like.objects.get_or_create(user=request.user, posting_content_type=self.posting_content_type, posting_object_id=posting_id)[0]
		return Response(like.posting.get_likes())


class PostReport(GratitudeStreamView):
	def post(self, request, posting_type, posting_id, format=None):
		self.get_posting_content_type(posting_type)
		Report.objects.get_or_create(user=request.user, posting_content_type=self.posting_content_type, posting_object_id=posting_id)[0]
		return Response()
