import apiclient
from datetime import datetime, timedelta
from dateutil import rrule
from dateutil.parser import parse
from oauth2client.django_orm import Storage

from django.conf import settings

from oauth2_hs.models import Credentials
from errors_hs.models import ErrorReport
from healers.models import (Healer, Appointment, UnavailableSlot, Timezone,
	is_wellness_center, WellnessCenterGoogleEventId)
from sync_hs.models import GOOGLE_API, UnavailableCalendar, CalendarSyncQueueTask
from sync_hs.google import GoogleClient


# def call_google_request(func):
# 	"""
# 	Decorator for google requests
# 	If except 302 Moved Temporary response or 500, try to send request again, limit 3 attempts
# 	"""
# 	def wrapper(*args, **kwargs):
# 		i = 0
# 		while True:
# 			try:
# 				result = func(*args, **kwargs)
# 				return result
# 			except RequestError as e:
# 				i += 1
# 				if e.status in [302, 500] and i < 3:
# 					time.sleep(2)
# 					continue
# 				else:
# 					raise e

# 	return wrapper


class GoogleCalendar(GoogleClient):
	"""Google calendars management, build and send requests."""

	def __init__(self, user):
		super(GoogleCalendar, self).__init__(user)
		self.service = self.build_service('calendar', 'v3')

	def batch_delete_event_callback(self, request_id, response, exception):
		if exception is not None:
			self.batch_errors += 1
			return

	def batch_add_event_callback(self, request_id, response, exception):
		if exception is not None:
			self.batch_errors += 1
			return
		try:
			appointment_id = int(response['extendedProperties']['private']['appointment_id'])
			appointment = self.batch_appointments[appointment_id]
			event_id = response['id']

			if not self.batch_wcenter:
				appointment.google_event_id = event_id
				appointment.save(google_sync=False)
			else:
				wcenter_event = WellnessCenterGoogleEventId.objects.get_or_create(
					wellness_center=self.batch_wcenter, appointment=appointment)[0]
				wcenter_event.google_event_id = event_id
				wcenter_event.save()
		except IndexError:
			self.batch_errors += 1

	def init_batch(self, callback):
		if self.batch is None:
			self.batch_errors = 0
			self.batch = apiclient.http.BatchHttpRequest(callback=callback)

	def clear(self, calendar_id):
		"""Clear calendar and return errors or None if success."""
		events = self.get_events(calendar_id, include_deleted=True)
		for event in events:
			self.batch_delete_event(calendar_id, event['id'])
		return self.execute_batch()

	def create(self, title, description, color, timezone):
		"""Create calendar and return calendar id."""
		calendar = {'summary': title,
			'description': description,
			'timezone': timezone}
		calendar = self.service.calendars().insert(body=calendar).execute()
		calendar_id = calendar['id']
		calendar_list_entry = {
			'id': calendar_id,
			# 'foregroundColor': color,
			'selected': True
		}
		try:
			self.service.calendarList().insert(body=calendar_list_entry).execute()
			return calendar_id
		except apiclient.errors.Error:
			self.delete(calendar_id)
			raise apiclient.errors.Error()

	def get_list(self):
		return self.service.calendarList().list(
			minAccessRole='owner').execute()['items']

	def delete_calendar(self, calendar_id):
		self.service.calendars().delete(calendarId=calendar_id).execute()

	def get_events(self, calendar_id, update_date=None, max_days=None, include_deleted=False):
		def format_time(time):
			return '%s%s' % (time.isoformat(), '.000Z')

		now = settings.GET_NOW().replace(microsecond=0)
		params = {
			'calendarId': calendar_id,
			'maxResults': 2500,
			'showDeleted': False,
			'singleEvents': True
		}
		params['timeMin'] = format_time(now)
		if max_days:
			params['timeMax'] = format_time(now + timedelta(days=max_days))
		if update_date:
			params['updatedMin'] = format_time(update_date.replace(microsecond=0))

		# print params
		response = self.service.events().list(**params).execute()
		return response['items']

	def init_event_entry(self, appointment, is_wellness_center):
		def get_recurrence_data():
			def recurrence_datetime_format(dt):
				return dt.isoformat().replace('-', '').replace(':', '')

			freq = {rrule.DAILY: 'DAILY', rrule.WEEKLY: 'WEEKLY', rrule.MONTHLY: 'MONTHLY'}
			data = []
			count = interval = ""
			if appointment.repeat_count:
				count = ";COUNT=%d" % appointment.repeat_count
			if appointment.repeat_every > 1:
				interval = ";INTERVAL=%d" % appointment.repeat_every
			data.append('RRULE:FREQ=%s%s%s' % (freq[appointment.repeat_period], count, interval))
			if appointment.exceptions:
				exceptions = ','.join([recurrence_datetime_format(datetime.utcfromtimestamp(ex)+timedelta(minutes=appointment.start_time))
										for ex in appointment.exceptions])
				data.append('EXDATE;TZID=%s:%s' % (tzid, exceptions))
			return data

		title = str(appointment.client)
		if is_wellness_center:
			title = '%s - %s' % (str(appointment.healer), title)

		event = {'summary': title,
			'description': appointment.event_info(),
			'location': appointment.location.address_text()}

		tzid = Timezone.TIMEZONE_CODES[appointment.healer.timezone]
		event.update({
			'start': {
				'dateTime': appointment.start.isoformat(),
				'timeZone': tzid
			},
			'end': {
				'dateTime': appointment.end.isoformat(),
				'timeZone': tzid
			}})
		if not appointment.is_single():
			event['recurrence'] = get_recurrence_data()

		event['extendedProperties'] = {'private': {
			'appointment_id': appointment.id
		}}

		return event

	def create_event_request(self, calendar_id, appointment, is_wellness_center):
		event = self.init_event_entry(appointment, is_wellness_center)
		return self.service.events().insert(calendarId=calendar_id, body=event)

	def create_event(self, calendar_id, appointment, is_wellness_center=False):
		"""Create event and return event id."""
		return self.create_event_request(calendar_id, appointment, is_wellness_center).execute()['id']

	def update_event(self, calendar_id, appointment, wcenter=False):
		"""Update event and return event id."""
		def get_event_id():
			if wcenter:
				try:
					return appointment.wellness_center_google_event_ids.get(wellness_center=wcenter).google_event_id
				except WellnessCenterGoogleEventId.DoesNotExist, e:
					ErrorReport.objects.create(report=str(e))
					return
			else:
				return appointment.google_event_id

		event_id = get_event_id()
		if event_id is not None:
			event = self.init_event_entry(appointment, is_wellness_center)
			return self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()['id']
		else:
			return self.create_event(calendar_id, appointment, wcenter)

	def delete_event_request(self, calendar_id, event_id):
		return self.service.events().delete(calendarId=calendar_id, eventId=event_id)

	def delete_event(self, calendar_id, event_id):
		self.delete_event_request(calendar_id, event_id).execute()

	def get_email(self):
		service = self.build_service('oauth2', 'v2')
		return service.userinfo().get().execute()['email']

	def add_appointment_to_batch(self, calendar_id, appointment, is_wellness_center):
		self.init_batch(self.batch_add_event_callback)
		self.batch.add(self.create_event_request(calendar_id, appointment, is_wellness_center))

	def batch_delete_event(self, calendar_id, event_id):
		self.init_batch(self.batch_delete_event_callback)
		self.batch.add(self.delete_event_request(calendar_id, event_id))

	def execute_appointments_batch(self, appointments, wcenter):
		self.batch_appointments = appointments
		self.batch_wcenter = wcenter
		return self.execute_batch()

	def execute_batch(self):
		"""Execute batch and return number of errors and 0 if no errors found.
		Return None if there is nothing in batch queue."""
		if self.batch is not None:
			self.batch.execute(http=self.http)
			self.batch = None
			return self.batch_errors


def reset_calendar(healer, google_calendar, soft_reset):
	"""Delete and create new calendar, sync appointments using batch request."""

	def create_google_calendar(healer, google_calendar):
		def remove_existing_calendars():
			"""Remove previous versions of calendar."""
			try:
				calendars_list = google_calendar.get_list()
				for calendar in calendars_list:
					if calendar['summary'] == Healer.GOOGLE_CALENDAR_TITLE and calendar['id'] != calendar_id:
						google_calendar.delete_calendar(calendar['id'])
			except apiclient.errors.Error:
				# Can't get list
				pass

		""" Create new google calendar using GoogleCalendar wrapper """
		calendar_id = google_calendar.create(title=Healer.GOOGLE_CALENDAR_TITLE,
												description='This calendar contains healersource appointments',
												color='#528800', timezone=Timezone.TIMEZONE_CODES[healer.timezone])
		email = google_calendar.get_email()
		healer.google_email = email
		healer.google_calendar_id = calendar_id
		healer.save()
		remove_existing_calendars()
		return calendar_id

	if soft_reset:
		calendar_id = healer.google_calendar_id
		errors = google_calendar.clear(calendar_id)
		if errors > 0:
			return errors
	else:
		calendar_id = create_google_calendar(healer, google_calendar)

	wcenter = is_wellness_center(healer)
	if wcenter:
		healers = wcenter.get_healers_in_wcenter()
		WellnessCenterGoogleEventId.objects.filter(wellness_center=wcenter).delete()
	else:
		healers = [healer]

	errors = 0
	appts_dict = {}
	for healer in healers:
		appts = Appointment.objects.filter(healer=healer,
			confirmed=True)
		if wcenter:
			appts = appts.filter(location__in=wcenter.get_location_ids())

		if not appts.exists():
			continue

		for appointment in appts:
			google_calendar.add_appointment_to_batch(calendar_id, appointment, wcenter)
			appts_dict[appointment.id] = appointment

	if appts_dict:
		errors = google_calendar.execute_appointments_batch(appts_dict, wcenter)
	return errors


def sync_unavailable_slots(healer, google_calendar):
		"""Get events from other calendars. Ignore requests from center."""

		def clear_slots_before_now():
			UnavailableSlot.objects.filter(healer=healer,
				api=GOOGLE_API).exclude_by_datetime(now).delete()

		def save_slot(calendar, title, event_id, start, end):
			slot = UnavailableSlot()
			slot.healer = healer
			slot.api = GOOGLE_API
			slot.calendar = calendar
			if title:
				slot.title = title
			slot.event_id = event_id
			slot.set_dates(start, end, True)
			if slot.end_date is None:
				slot.end_date = slot.start_date
			slot.save()
			return slot

		def get_datetime(event_date):
			date = event_date.get('dateTime', False)
			if not date:
				date = event_date['date']
			return parse(date, ignoretz=True)

		def delete_removed_slots(calendar, event_ids):
			current_unavailable_slots_events_ids = UnavailableSlot.objects.filter(
				calendar=calendar, healer=healer, api=GOOGLE_API).values_list('event_id', flat=True)
			slots_event_ids_to_remove = set(current_unavailable_slots_events_ids) - set(event_ids)
			UnavailableSlot.objects.filter(calendar=calendar, healer=healer, api=GOOGLE_API, event_id__in=slots_event_ids_to_remove).delete()

		# ignore center request
		if is_wellness_center(healer):
			return

		added_slots = []
		now = healer.get_local_time()
		clear_slots_before_now()

		for calendar in UnavailableCalendar.objects.filter(healer=healer, api=GOOGLE_API):
			# print calendar
			try:
				events = google_calendar.get_events(calendar.calendar_id, calendar.update_date, healer.bookAheadDays * 2)
			except apiclient.errors.HttpError as err:
				if err.resp.status == 503:
					events = []
				else:
					raise
			# print events

			delete_removed_slots(calendar, [event['id'] for event in events])

			event_exclude_list = {}
			for event in events:
				event_id = event['id']
				if 'recurringEventId' in event:
					original_event_id = event['recurringEventId']
					start = get_datetime(event['originalStartTime'])
					UnavailableSlot.objects.filter(event_id=original_event_id,
													start_date=start.date()).delete()
					if original_event_id not in event_exclude_list:
						event_exclude_list[original_event_id] = []
					event_exclude_list[original_event_id].append(start.date())
				UnavailableSlot.objects.filter(event_id=event_id).delete()
				if event['status'] == 'confirmed':
					start = get_datetime(event['start'])
					end = get_datetime(event['end'])
					if end > now and start.date() not in event_exclude_list.get(event_id, []):
						slot = save_slot(calendar, event.get('summary', False), event_id, start, end)
						added_slots.append(slot)

			calendar.update_date = now
			calendar.save()
		return added_slots


def disable_google_sync(healer):
	healer.google_calendar_id = ''
	healer.google_email = ''
	healer.save()
	Storage(Credentials, 'id', healer.user, 'google_credential').delete()
	UnavailableCalendar.objects.filter(healer=healer, api=GOOGLE_API).delete()

	UnavailableCalendar.objects.filter(healer=healer, api=GOOGLE_API).delete()
	UnavailableSlot.objects.filter(healer=healer, api=GOOGLE_API).delete()

	Appointment.objects.filter(healer=healer).update(google_event_id='')

	wcenter = is_wellness_center(healer)
	if wcenter:
		WellnessCenterGoogleEventId.objects.filter(wellness_center=wcenter).delete()
	task_filter_data = {CalendarSyncQueueTask.get_object_name(wcenter): healer, 'api': GOOGLE_API}
	CalendarSyncQueueTask.objects.filter(**task_filter_data).delete()
