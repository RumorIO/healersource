from StringIO import StringIO
import oauth2client
import apiclient

# from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.context import RequestContext

from rest_framework.response import Response

from account_hs.authentication import user_authenticated
from healers.models import Healer, is_wellness_center
from healers.views import HealerAuthenticated
from sync_hs.forms import TimezoneForm, UnavailableCalendarsForm
from sync_hs.gcalendar import (GoogleCalendar, reset_calendar,
								sync_unavailable_slots, disable_google_sync)
from sync_hs.models import CalendarSyncStatus, GOOGLE_API, UnavailableCalendar


def reset_gcal(healer, user, soft_reset=False):
	"""Reset calendar. Return error code #.
	1 - sync has already started, any other error
	2 - authentication error
	"""
	try:
		google_calendar = GoogleCalendar(user)
		if CalendarSyncStatus.objects.is_running(user, GOOGLE_API):
			return 1
		CalendarSyncStatus.objects.start(user, GOOGLE_API)
		UnavailableCalendar.objects.filter(healer=healer,
			api=GOOGLE_API).update(update_date=None)
		reset_calendar(healer, google_calendar, soft_reset)
		sync_unavailable_slots(healer, google_calendar)
	except oauth2client.client.Error:
		return 2
	except (Healer.DoesNotExist, apiclient.errors.Error):
		return 1
	finally:
		CalendarSyncStatus.objects.stop(user, GOOGLE_API)


class Reset(HealerAuthenticated):
	def reset(self, soft_reset=False):
		self.get_initial_data()
		error = reset_gcal(self.healer, self.request.user, soft_reset)
		if error is None:
			result = 'Success'
		elif error == 1:
			result = None
		elif error == 2:
			result = 'Access Denied'
		return Response(result)


class HardReset(Reset):
	""" Recreate google calendar and update it with current appointments. """
	def post(self, request, format=None):
		return self.reset()


class SoftReset(Reset):
	""" Reset google calendar and update it with current appointments. """
	def post(self, request, format=None):
		return self.reset(True)


class Sync(HealerAuthenticated):
	def post(self, request, format=None):
		self.get_initial_data()
		try:
			output = StringIO()
			call_command('calendar_sync', healer=self.healer, verbose=0, interactive=False, stdout=output)
			output.seek(0)
			data = '<br>'.join(output.readlines())
		except:
			return Response()
		return Response({
			'status': 'Success',
			'data': data})


@user_authenticated
def google_calendar_instruction(request, template_name="healers/google_calendar.html"):
	""" Google calendar instruction page """
	healer = get_object_or_404(Healer, user__id=request.user.id)
	if healer.google_email:
		form = None
		if not is_wellness_center(healer):
			try:
				google_calendar = GoogleCalendar(request.user)
				calendars = google_calendar.get_list()
				calendars_choices = {}
				for calendar in calendars:
					if calendar['id'] != healer.google_calendar_id:
						calendars_choices[calendar['id']] = calendar['summary']

				if request.POST:
					form = UnavailableCalendarsForm(request.POST, calendars_choices=calendars_choices.items())
					if form.is_valid():
						updated_calendars = []
						for calendar_id in form.cleaned_data['calendars']:
							calendar, created = UnavailableCalendar.objects.get_or_create(healer=healer,
																							api=GOOGLE_API,
																							calendar_id=calendar_id,
																							title=calendars_choices[calendar_id])
							updated_calendars.append(calendar.id)
						UnavailableCalendar.objects.filter(healer=healer,
															api=GOOGLE_API).exclude(id__in=updated_calendars).delete()
					call_command('calendar_sync', healer=healer, verbose=0, interactive=False)
				else:
					calendars_ids = UnavailableCalendar.objects.values_list('calendar_id', flat=True).filter(healer=healer,
																										api=GOOGLE_API)
					form = UnavailableCalendarsForm(calendars_choices=calendars_choices.items(),
												initial={'calendars': calendars_ids})
			except oauth2client.client.Error:
				return redirect('oauth2_google_login')
			except apiclient.errors.Error:
				pass

	else:
		form = TimezoneForm(initial={"timezone": healer.timezone})

	return render_to_response(template_name, {
		"healer": healer,
		"form": form
	}, context_instance=RequestContext(request))


@user_authenticated
def google_calendar_disable(request, change=False):
	""" Clear google calendar links from healer and appointments. """
	healer = get_object_or_404(Healer, user=request.user)
	disable_google_sync(healer)
	# messages.add_message(request, messages.SUCCESS, "Google Calendar Sync disabled.")
	if change:
		return HttpResponseRedirect(reverse('google_calendar_sync_run'))
	return HttpResponseRedirect(reverse('google_calendar_instruction'))


@user_authenticated
def google_calendar_sync(request, run=False):
	""" Create google calendar and update it with current appointments. """

	healer = get_object_or_404(Healer, user=request.user)

	if request.method == 'POST' or run:
		if request.method == 'POST':
			form = TimezoneForm(request.POST)
			if form.is_valid():
				healer.timezone = form.cleaned_data['timezone']
				healer.save()

		error = reset_gcal(healer, request.user)
		if error == 2:
			return redirect('oauth2_google_login')

	return HttpResponseRedirect(reverse('google_calendar_instruction'))
	# messages.add_message(request, messages.ERROR, 'Could not sync with google calendar. Try again later.')
	# messages.add_message(request, messages.WARNING, 'Google calendar synced with errors. Try again later.')
	# messages.add_message(request, messages.SUCCESS, 'Google calendar synced.')
