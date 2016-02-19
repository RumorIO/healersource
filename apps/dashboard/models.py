from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from dashboard.services.mailprocessors import MAIL_PROCESSORS, \
	MAIL_PROCESSOR_DEFAULT


@python_2_unicode_compatible
class HealerSettings(models.Model):
	key = models.SlugField('key', primary_key=True)
	description = models.CharField('description', max_length=254)
	value = models.TextField('value')
	type = models.CharField('unused', max_length=254, null=True, blank=True)
	web_only = models.BooleanField('can change only by web (here)',
								   default=True, db_index=True)

	def __str__(self):
		return '%s' % self.key


@python_2_unicode_compatible
class HealerActions(models.Model):
	action = models.CharField('action', max_length=254, db_index=True)
	created = models.DateTimeField(auto_now_add=True, db_index=True)

	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey()

	class Meta:
		unique_together = ['action', 'content_type', 'object_id']

	def __str__(self):
		return '%s on %s' % self.action, self.content_object


@python_2_unicode_compatible
class HealerMails(models.Model):
	slug = models.SlugField('email id', unique=True)

	title = models.CharField('title', max_length=254)
	body = models.TextField('body')
	body_html = models.TextField('html', null=True, blank=True)
	email_from = models.EmailField(max_length=255, null=True, default=None)
	delay = models.PositiveIntegerField('delay in days')

	once = models.BooleanField('send only once', db_index=True, default=False)

	process = models.CharField('processor', choices=MAIL_PROCESSORS,
							   default=MAIL_PROCESSOR_DEFAULT,
							   max_length=254, db_index=True)

	def __str__(self):
		return '%s' % self.title
