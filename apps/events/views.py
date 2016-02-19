from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from rest_framework.response import Response

from account_hs.authentication import user_authenticated
from account_hs.views import UserAuthenticated
from healers.forms import NewUserForm
from healers.models import Healer
from clients.forms import ClientLocationForm
from clients.models import ClientLocation
from clients.utils import get_person_content_type
from events.models import Event, EventsManager, EventAttendee
from events.forms import EventForm, EventLocationDateForm, EventsFilterForm


def event(request, event_id):
	event = get_object_or_404(Event, pk=event_id)
	return render_to_response('events/event.html',
		{'event': event}, context_instance=RequestContext(request))


def events(request):
	form = EventsFilterForm(request.GET or None)
	events = Event.objects.current(ordered=False)
	if form.is_valid():
		type = form.cleaned_data['type']
		text = form.cleaned_data['text']
		if type:
			events = events.filter(type=type)
		if text:
			events = events.filter(Q(title__icontains=text) | Q(description__icontains=text))
	events = EventsManager.order(events)
	return render_to_response('events/events.html',
		{'events': events, 'form': form}, context_instance=RequestContext(request))


class EditEvent(TemplateView):
	template_name = 'events/edit_event.html'

	def get_forms_and_event(self, client, event_id, data=None):
		def get_event_location_date():
			location_dates = event.location_dates
			if location_dates.exists():
				return location_dates.all()[0]

		if event_id is None:
			event = None
			location_date = None
		else:
			event = get_object_or_404(Event, pk=event_id, client=client)
			location_date = get_event_location_date()

		event_form = EventForm(data, instance=event)
		event_location_date_form = EventLocationDateForm(data,
			client=client, instance=location_date)
		location_form = ClientLocationForm(data, prefix='location')
		return event_form, event_location_date_form, location_form, event

	def get(self, request, *args, **kwargs):
		client = request.user.client
		event_id = kwargs.get('event_id', None)
		event_form, event_location_date_form, location_form, event = self.get_forms_and_event(client, event_id)

		context = self.get_context_data(*args, **kwargs)

		if event is not None:
			context['new_user_form'] = NewUserForm()
			context['event'] = event

		context.update({
			'event_form': event_form,
			'event_location_date_form': event_location_date_form,
			'location_form': location_form,
		})

		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		client = request.user.client
		event_id = kwargs.get('event_id', None)
		event_form, event_location_date_form, location_form, _ = self.get_forms_and_event(client, event_id, request.POST)

		context = {}

		if event_form.is_valid():
			event = event_form.save(commit=False)
			event.client = client
			if 'photo' in request.FILES:
				event.photo = request.FILES['photo']
			event.save()
			event_form = EventForm(instance=event)

			if event_location_date_form.data['location'] == 'new_location':
				if location_form.is_valid():
					location = location_form.save()
					ClientLocation.objects.create(client=client, location=location)
					data = event_location_date_form.data
					data['location'] = location.pk
					event_location_date_form = EventLocationDateForm(data,
						client=client, instance=event_location_date_form.instance)
			else:
				location_form = ClientLocationForm(prefix='location')

			if event_location_date_form.is_valid():
				location_date = event_location_date_form.save()
				event.location_dates.add(location_date)

			context['new_user_form'] = NewUserForm()
			context['event'] = event
		else:
			location_form = ClientLocationForm(prefix='location')
			self.template_name = 'events/create_event.html'

		context.update({
			'event_form': event_form,
			'event_location_date_form': event_location_date_form,
			'location_form': location_form,
		})
		if 'event' in context:
			kwargs['event'] = event
		context.update(self.get_context_data(*args, **kwargs))
		return render(request, self.template_name, context)


class ListEvents(EditEvent):
	history = False
	template_name = 'events/list_events.html'

	def get_context_data(self, *args, **kwargs):
		event = kwargs.pop('event', None)
		context = super(ListEvents, self).get_context_data(*args, **kwargs)

		def get_events():
			if self.history:
				return Event.objects.past(client=client)
			else:
				return Event.objects.current(client=client)

		client = self.request.user.client
		if event is not None:
			if event.is_past():
				self.history = True
			else:
				event_form, event_location_date_form, location_form, _ = self.get_forms_and_event(client, None)
				context.update({
					'event_form': event_form,
					'event_location_date_form': event_location_date_form,
					'location_form': location_form,
				})
		context.update({'events': get_events(),
			'history': self.history,
			'new_user_form': NewUserForm()})
		return context


@user_authenticated
def remove_event(request, event_id):
	client = request.user.client
	event = get_object_or_404(Event, pk=event_id, client=client)
	event.delete()
	return redirect('list_events')


class EventView(UserAuthenticated):
	def get_initial_data(self, event_id):
		self.event = get_object_or_404(Event, pk=event_id, client=self.request.user.client)


class HostAdd(EventView):
	def post(self, request, event_id, healer_id, format=None):
		self.get_initial_data(event_id)
		host = get_object_or_404(Healer, pk=healer_id)
		html = ''
		if host not in self.event.hosts.all():
			self.event.hosts.add(host)
			html = render_to_string('events/host_row.html', {
				'event': self.event,
				'host': host})
		return Response(html)


class HostRemove(EventView):
	def post(self, request, event_id, healer_id, format=None):
		self.get_initial_data(event_id)
		host = get_object_or_404(Healer, pk=healer_id)
		self.event.hosts.remove(host)
		return Response()


class ShowAttendees(EventView):
	def get(self, request, event_id, format=None):
		self.get_initial_data(event_id)
		html = render_to_string('events/attendees.html', {
			'attendees': self.event.attendees.all(),
			'event': self.event})
		return Response(html)


class AttendeeAdd(EventView):
	def post(self, request, event_id, person_type, person_id, format=None):
		self.get_initial_data(event_id)
		type = self.request.POST.get('type', False)
		if type == 'full':
			template = 'events/attendee_full_row.html'
		else:
			template = 'events/attendee_row.html'
		attendee = EventAttendee.objects.get_or_create(person_content_type=get_person_content_type(person_type),
				person_object_id=person_id)[0]
		html = ''
		if attendee not in self.event.attendees.all():
			self.event.attendees.add(attendee)
			html = render_to_string(template, {
				'event': self.event,
				'attendee': attendee})
		return Response(html)


class AttendeeRemove(EventView):
	def post(self, request, event_id, attendee_id, format=None):
		self.get_initial_data(event_id)
		attendee = get_object_or_404(EventAttendee, pk=attendee_id)
		self.event.attendees.remove(attendee)
		return Response()
