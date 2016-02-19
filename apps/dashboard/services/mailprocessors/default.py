# coding=utf-8
from django.contrib.auth import get_user_model


PROCESSOR = ('default', 'Default processor')


class MailProcessor(object):
	def __init__(self, template, context, user, **kwargs):
		self.template = template
		self.context = context
		self.kwargs = kwargs
		self.user = user

	def get_users(self):
		if isinstance(self.user, get_user_model()):
			return [self.user]
		elif isinstance(self.user, int):
			return [get_user_model().objects.get(pk=self.user)]
		elif isinstance(self.user, str):
			return [self.user]
		elif isinstance(self.user, list):
			return self.user
		else:
			return get_user_model().objects.filter(is_active=True)

	def get_email_from_user(self, user):
		if isinstance(user, str):
			return user
		return user.email

	def get_single_context(self, **kwargs):
		kwargs.update(self.kwargs)
		return kwargs

	def post_sent(self, user):
		pass
