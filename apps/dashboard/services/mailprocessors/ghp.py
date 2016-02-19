# coding=utf-8
from calendar import mdays
from datetime import timedelta, date
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from emailconfirmation.models import EmailAddress
from dashboard.models import HealerActions
from dashboard.services.mailprocessors.default import \
	MailProcessor as DefaultProcessor
from dashboard.utils import create_action
from clients.models import Client
from send_healing.models import SentHealing

GHP_NOTIFICATION_SENT = 'ghp_notification_sent'

PROCESSOR = ('ghp', 'Global Healing Project processor')


class MailProcessor(DefaultProcessor):
	def filter_sent_healing(self, clients):
		return SentHealing.objects.filter(person_content_type__model='client',
				person_object_id__in=clients, started_at__range=(self.date_start, self.date_end))

	def get_healers(self, healing_received):
		healers_users = healing_received.values_list('sent_by__user', flat=True).distinct()
		return Client.objects.filter(user__in=healers_users)

	def get_users(self):
		def first_day_of_month(d):
			return date(d.year, d.month, 1)

		def get_healing_received():
			clients = Client.objects.filter(user__in=users_to_send).values_list('pk', flat=True)
			return self.filter_sent_healing(clients)

		def exclude_users_without_healing_received():
			clients_ids = healing_received.values_list('person_object_id', flat=True)
			return Client.objects.filter(pk__in=clients_ids).values_list('user__pk', flat=True).distinct()

		user_ct = ContentType.objects.get_for_model(get_user_model())
		if self.template.delay == 1:
			self.frequency = 'daily'
			self.date_start = timezone.now().date()
			self.date_end = self.date_start + timedelta(days=1)
		elif self.template.delay == 7:
			self.frequency = 'weekly'
			self.date_start = first_day_of_month(timezone.now().date())
			self.date_end = self.date_start + timedelta(mdays[self.date_start.month])

		users_with_notifications_on = Client.objects.filter(
			ghp_notification_frequency=self.frequency).values_list('user__id', flat=True)

		users_with_notification_sent = HealerActions.objects \
			.values_list('object_id', flat=True) \
			.filter(action=GHP_NOTIFICATION_SENT,
				content_type_id=user_ct.pk,
				created__gte=self.date_start,
				created__lt=self.date_end)

		users_to_send = list(set(users_with_notifications_on) - set(users_with_notification_sent))
		healing_received = get_healing_received()
		users_to_send = exclude_users_without_healing_received()

		self.context = {'healers': self.get_healers(healing_received)}
		return User.objects.filter(pk__in=users_to_send)

	def get_email_from_user(self, user):
		emails = EmailAddress.objects.filter(user=user, verified=True,
			primary=True)
		if len(emails) > 0:
			return emails[0].email
		else:
			return user.email

	def get_single_context(self, user):
		client_id = Client.objects.get(user=user).pk
		healing_received = self.filter_sent_healing([client_id])
		return {'healers': self.get_healers(healing_received)}

	def post_sent(self, user):
		create_action(GHP_NOTIFICATION_SENT, user)
