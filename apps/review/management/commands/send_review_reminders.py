from datetime import timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from healers.utils import send_hs_mail, get_full_url
from healers.models import Appointment, Healer
from review.models import Review

class Command(BaseCommand):

	help = 'Send review reminders for yesterday appointments to clients'

	def handle(self, *args, **options):
		today = datetime.combine(settings.GET_NOW(), time())
		appts = Appointment.objects.filter(confirmed=True).exclude(healer__review_permission=Healer.VISIBLE_DISABLED)
		self.process_appts(appts.filter(repeat_period__isnull=True).filter_by_date(today-timedelta(days=2), today-timedelta(days=1)))  # single
		self.process_appts(appts.filter(repeat_period__isnull=False).filter_by_date(today-timedelta(days=2))) # repeat

	def process_appts(self, appts):
		for appt in appts:
			if Review.objects.filter(reviewer=appt.client, healer=appt.healer).count():
				continue

			today = appt.healer.get_local_time()
			yesterday = datetime.combine(today, time()) - timedelta(days=1)
			if appt.start_date == yesterday.date():
				self.send_reminders(appt.healer, appt.client)
			elif not appt.is_single():
				next_date = appt.find_next_in_rule(yesterday - timedelta(days=1))[0]
				if next_date == yesterday.date():
					self.send_reminders(appt.healer, appt.client)

	def send_reminders(self, healer, client):
		if not client.user.email:
			return

		ctx = {
			'healer_name': unicode(healer.user.client),
			'healer_first_name': healer.user.first_name.encode('ascii','replace'),
			'review_url': get_full_url('review_form', args=[healer.user.username])
		}
		from_email = settings.DEFAULT_FROM_EMAIL
		subject = render_to_string('review/emails/reminder_subject.txt', ctx)
		send_hs_mail(subject, 'review/emails/reminder_message.txt', ctx, from_email, [client.user.email])
