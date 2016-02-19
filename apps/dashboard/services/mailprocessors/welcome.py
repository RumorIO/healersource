# coding=utf-8
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from emailconfirmation.models import EmailAddress
from dashboard import EMAIL_VERIFIED
from dashboard.models import HealerActions
from dashboard.services.mailprocessors.default import \
	MailProcessor as DefaultProcessor
from dashboard.utils import create_action
from healers.models import Healer


WELCOME_SENT = 'welcome_sent'


PROCESSOR = ('welcome', 'Welcome mail processor')


class MailProcessor(DefaultProcessor):
	def get_users(self):
		user_ct = ContentType.objects.get_for_model(get_user_model())

		date_joined = Healer.objects \
			.values_list('user__id', flat=True) \
			.filter(
				user__date_joined__lt=timezone.now() - timedelta(days=self.template.delay),
				user__date_joined__gt=timezone.now() - timedelta(days=self.template.delay+11)
			)

		welcome_sent = HealerActions.objects \
			.values_list('object_id', flat=True) \
			.filter(action=WELCOME_SENT,
		           content_type_id=user_ct.pk
			)

		ready_list = set(date_joined) - set(welcome_sent)

		healers = Healer.objects.filter(user__in=ready_list)

		return [h.user for h in healers]

	def get_email_from_user(self, user):
		emails = EmailAddress.objects.filter(user=user, verified=True,
		                                     primary=True)
		if len(emails) > 0:
			return emails[0].email
		else:
			return user.email

	def post_sent(self, user):
		create_action(WELCOME_SENT, user)
