# import sys
import oauth2client
import apiclient
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.db.models.query_utils import Q

from healers.models import (Healer, WellnessCenterGoogleEventId,
	WellnessCenter, is_wellness_center)
from errors_hs.models import ErrorReport
from healers.utils import send_hs_mail, get_full_url
from util.timeout import Timeout, TimeoutError
from sync_hs.gcalendar import (GoogleCalendar, sync_unavailable_slots,
								disable_google_sync)
from sync_hs.models import *


class Command(BaseCommand):

	help = 'Sync appointments from queue to google calendar'

	def handle(self, healer=None, *args, **options):
		def error_report(type, e):
			report = 'Google Calendar Error #{} {} {}'.format(type, str(e), traceback.format_exc())
			ErrorReport.objects.create(report=report)
			if type in [2, 3, 5]:  # any exceptions excluding google / auth errors
				mail_admins('Google Sync Error', report)
			return report

		def get_google_calendar(healer):
			try:
				google_calendar = GoogleCalendar(healer.user)
				healer.google_calendar_sync_retries = 0
			except oauth2client.client.Error:
				healer.google_calendar_sync_retries += 1
				google_calendar = None
				# exc_type = sys.exc_info()[0]
				# error_report(1, "Cal Sync Error %s - %s - %s" % (exc_type, str(e), healer.user))
				if healer.google_calendar_sync_retries >= settings.MAX_GCAL_SYNC_RETRIES:
					disable_google_sync(healer)
					send_hs_mail('Google Calendar Sync Disabled',
						'sync_hs/email_calendar_disabled.txt',
						{'MAX_GCAL_SYNC_RETRIES': settings.MAX_GCAL_SYNC_RETRIES,
						'google_calendar_sync_link': get_full_url('google_calendar_instruction')},
						settings.DEFAULT_FROM_EMAIL, [healer.user.email],
						bcc=[admin[1] for admin in settings.ADMINS])
					healer.google_calendar_sync_retries = 0
			healer.save()
			return google_calendar

		def sync_cal(wcenter_sync=False):
			def get_objects():
				"""Return healers or centers who have sync tasks."""
				def get_ids():
					ids = CalendarSyncQueueTask.objects.values_list(object_name, flat=True).filter(api=GOOGLE_API)
					if wcenter_sync:
						ids = ids.exclude(wellness_center=None)
					else:
						ids = ids.filter(wellness_center=None)
					return ids.distinct()

				if wcenter_sync:
					model = WellnessCenter
				else:
					model = Healer

				objects = model.objects.filter(id__in=get_ids())
				if healer is not None:
					objects = objects.filter(user=healer.user)
				return objects

			def task_error(task, type, e):
				report = error_report(type, e)
				task.status = STATUS_FAIL
				task.save()
				if task.attempts > CalendarSyncQueueTask.MAX_ATTEMPTS:
					report = 'username - %s, email - %s, %s' % (object.user, object.user.email, report)
					mail_admins('CalendarSyncQueueTask Max Errors', report)

			object_name = CalendarSyncQueueTask.get_object_name(wcenter_sync)
			objects = get_objects()

			for object in objects:
				if CalendarSyncStatus.objects.is_running(object.user, GOOGLE_API):
					continue
				try:
					CalendarSyncStatus.objects.start(object.user, GOOGLE_API)
					google_calendar = get_google_calendar(object)
					if google_calendar is None:
						CalendarSyncStatus.objects.stop(object.user, GOOGLE_API)
						continue

					filter_data = {object_name: object}
					status_filter = Q(status=STATUS_WAITING) | (Q(status=STATUS_FAIL) & Q(attempts__lte=CalendarSyncQueueTask.MAX_ATTEMPTS))
					tasks = CalendarSyncQueueTask.objects.filter(api=GOOGLE_API, **filter_data).filter(status_filter)
					if wcenter_sync:
						wcenter = object
					else:
						wcenter = False
						tasks = tasks.filter(wellness_center=None)

					for task in tasks:
						task.status = STATUS_RUNNING
						task.attempts += 1
						task.save()
						try:
							with Timeout(20):
								event_id = None
								if task.action == ACTION_NEW:
									event_id = google_calendar.create_event(object.google_calendar_id, task.appointment, wcenter_sync)
									self.stdout.write('Event new, %s' % task.appointment)
								if task.action == ACTION_UPDATE:
									event_id = google_calendar.update_event(object.google_calendar_id, task.appointment, wcenter)
									self.stdout.write('Event update, %s' % task.appointment)
								if task.action == ACTION_DELETE:
									if wcenter_sync:
										wcenter_event = task.appointment.wellness_center_google_event_ids.get(
											wellness_center=wcenter)
										google_calendar.delete_event(object.google_calendar_id, wcenter_event.google_event_id)
										wcenter_event.delete()
									else:
										google_calendar.delete_event(object.google_calendar_id, task.appointment.google_event_id)
										self.stdout.write('Event delete, %s' % task.appointment)

								if wcenter_sync:
									if event_id is not None:
										wcenter_event = WellnessCenterGoogleEventId.objects.get_or_create(
												wellness_center=wcenter,
												appointment=task.appointment)[0]
										wcenter_event.google_event_id = event_id
										wcenter_event.save()
								else:
									if event_id is not None:
										task.appointment.google_event_id = event_id
									else:
										task.appointment.google_event_id = ''
									task.appointment.save(google_sync=False)

						except apiclient.errors.Error as e:
							# save error to find out the reason for error
							task_error(task, 4, e)
							continue

							#  left from gdata cal
							# if e.status == 403 and e.body == 'Cannot delete a cancelled event':
							# pass
						except TimeoutError:
							task.status = STATUS_FAIL
							task.save()
						except Exception as e:
							task_error(task, 2, e)
							continue

						task.delete()
				except Exception as e:
					error_report(3, e)
				finally:
					CalendarSyncStatus.objects.stop(object.user, GOOGLE_API)

		def sync_unavailable_cals():
			def remove_deleted_calendars():
				calendars = google_calendar.get_list()
				google_calendars_ids = [c['id'] for c in calendars]
				hs_calendars_ids = UnavailableCalendar.objects.values_list(
					'calendar_id', flat=True).filter(healer=h, api=GOOGLE_API)
				for cal_id in hs_calendars_ids:
					if cal_id not in google_calendars_ids:
						UnavailableCalendar.objects.get(healer=h, api=GOOGLE_API, calendar_id=cal_id).delete()

			healers_ids = UnavailableCalendar.objects.all().values_list('healer__pk', flat=True).distinct()
			healers = Healer.objects.filter(pk__in=healers_ids)
			if healer is not None:
				healers = healers.filter(pk=healer.pk)
			for h in healers:
				google_calendar = get_google_calendar(h)
				if google_calendar is None:
					continue
				remove_deleted_calendars()
				try:
					added_slots = sync_unavailable_slots(h, google_calendar)
					# for slot in added_slots:
					# 	self.stdout.write('Unavailable slot added - %s' % slot)
				except Exception as e:
					error_report(5, e)

		if healer is None:
			sync_cal(wcenter_sync=True)
			sync_cal()
			sync_unavailable_cals()
		else:
			if is_wellness_center(healer):
				sync_cal(wcenter_sync=True)
			else:
				sync_cal()
				sync_unavailable_cals()
