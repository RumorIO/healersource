from datetime import timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.conf import settings
from healers.models import Appointment

class Command(BaseCommand):

	help = 'Send appointment reminders for clients and providers the day before'

	def handle(self, *args, **options):
		today = datetime.combine(settings.GET_NOW(), time())
		appts = Appointment.objects.filter(confirmed=True, client__send_reminders=True)
		self.process_appts(appts.filter(repeat_period__isnull=True).filter_by_date(today-timedelta(days=1), today+timedelta(days=2)))  # single
		self.process_appts(appts.filter(repeat_period__isnull=False).filter_by_date(today-timedelta(days=1))) # repeat

	def process_appts(self, appts):
		for appt in appts:
			today = appt.healer.get_local_time()
			tomorrow = datetime.combine(today, time()) + timedelta(days=1)
			if appt.start_date == tomorrow.date():
				self.send_reminders(appt)
			elif not appt.is_single():
				next_date = appt.find_next_in_rule(today)[0]
				if next_date == tomorrow.date():
					self.send_reminders(appt)

	def send_reminders(self, appt):
		appt.send_reminder(appt.healer.user)
