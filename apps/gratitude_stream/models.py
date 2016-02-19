from django.db import models
from mezzanine.generic.models import ThreadedComment
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType


class SpammingUser(models.Model):
	user = models.OneToOneField(User)

	def __unicode__(self):
		return unicode(self.user)


class Question(models.Model):
	text = models.CharField(default='', max_length=100)

	def __unicode__(self):
		return self.text


class PostingActionAbstract(models.Model):
	user = models.ForeignKey(User)
	posting_content_type = models.ForeignKey(ContentType)
	posting_object_id = models.PositiveIntegerField()
	posting = generic.GenericForeignKey('posting_content_type', 'posting_object_id')

	class Meta:
		abstract = True


class Like(PostingActionAbstract):
	pass


class Report(PostingActionAbstract):
	pass


class PostingManager(models.Manager):
	def get_queryset(self):
		spamming_users = SpammingUser.objects.all().values_list('user__pk', flat=True)
		return super(PostingManager, self).get_queryset().exclude(user__in=spamming_users)


class PostingAbstract(models.Model):
	def type(self):
		if getattr(self, 'text', None) is not None:
			return 'post'
		else:
			return 'postcomment'

	def content(self):
		if self.type() == 'post':
			return self.text
		else:
			return self.comment

	def get_likes(self):
		content_type = ContentType.objects.get(app_label='gratitude_stream', model=self.type())
		return Like.objects.filter(posting_content_type=content_type, posting_object_id=self.pk).count()

	objects = PostingManager()

	class Meta:
		abstract = True
		ordering = ['-pk']


class Post(PostingAbstract):
	user = models.ForeignKey(User)
	question = models.ForeignKey(Question)
	text = models.CharField(default='', max_length=100)
	submit_date = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return self.text


class PostComment(PostingAbstract, ThreadedComment):
	pass
