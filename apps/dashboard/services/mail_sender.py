from copy import copy
from django.conf import settings
from django.contrib.sites.models import Site
from django.template import loader, Context, Template
from django.utils import importlib
from dashboard.models import HealerMails


class MailSenderNoTemplateException(Exception):
	pass


class MailSender(object):
	def __init__(self, template, user=None, **kwargs):
		self.kwargs = kwargs
		self.kwargs['user'] = user
		try:
			self.template = HealerMails.objects.get(slug=template)
		except HealerMails.DoesNotExist as e:
			raise MailSenderNoTemplateException(e)
		self.processor = self.get_processor()

	def get_context(self):
		return Context({
			'site': Site.objects.get_current(),
			'template': self.template.slug
		})

	def get_processor(self):
		m = importlib.import_module(
			'dashboard.services.mailprocessors.%s' % self.template.process)
		return m.MailProcessor(self.template, self.get_context(), **self.kwargs)

	def send_email(self, user, message, message_html=None):
		def get_reply_to():
			if self.template.slug == 'welcome_mail':
				return settings.WELCOME_EMAIL_REPLY_TO

		from healers.utils import send_html_mail, send_regular_mail
		email = self.processor.get_email_from_user(user)
		context = Context({})
		if not message_html:
			body_html = message.replace('\n', '<br />')
			context.update({'body': body_html})
			message_html = loader.render_to_string('email_blank_base.html',
													context)

		if settings.EMAIL_DEBUG:
			if message_html:
				msg = message_html
			else:
				msg = message
			send_regular_mail(self.template.title, msg,
				settings.DEFAULT_FROM_EMAIL, [email, ], fail_silently=True,
				reply_to=get_reply_to())
		else:
			send_html_mail(self.template.title, message, message_html,
			               (self.template.email_from if self.template.email_from else settings.MESSAGE_PROCESSOR_FROM_EMAIL),
			                [email, ], fail_silently=True, reply_to=get_reply_to())

		self.processor.post_sent(user)

	def send_emails(self):
		t = Template(self.template.body)
		t_html = None
		if (self.template.body_html is not None and
				self.template.body_html.strip() != ''):
			t_html = Template(self.template.body_html)

		for user in self.processor.get_users():
			context = copy(self.processor.context)
			context.update(self.processor.get_single_context(user=user))
			if type(context) == dict:
				context = Context(context)
			context.update(self.get_context())
			message = t.render(context)
			message_html = None
			if t_html:
				message_html = t_html.render(context)
			self.send_email(user, message, message_html)
