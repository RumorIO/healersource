from django.conf.urls import patterns, url

from account_hs.authentication import user_authenticated
from events.views import (EditEvent, ListEvents, HostAdd, HostRemove,
	ShowAttendees, AttendeeAdd, AttendeeRemove)

urlpatterns = patterns("",
	url(r"^$", "events.views.events", name="events"),
	url(r"^(?P<event_id>[0-9]+)$", "events.views.event", name="event"),

	url(r"^(?P<event_id>[0-9]+)/edit/$", user_authenticated(EditEvent.as_view()), name="event_edit"),
	url(r"^(?P<event_id>[0-9]+)/remove/$", "events.views.remove_event", name="event_remove"),
	url(r"^(?P<event_id>[0-9]+)/host/add/$", 'util.views.page_not_found', name="event_add_host"),
	url(r"^(?P<event_id>[0-9]+)/host/add/(?P<healer_id>[0-9]+)/$", HostAdd.as_view(), name="event_add_host"),
	url(r"^(?P<event_id>[0-9]+)/host/remove/$", 'util.views.page_not_found', name="event_remove_host"),
	url(r"^(?P<event_id>[0-9]+)/host/remove/(?P<healer_id>[0-9]+)/$", HostRemove.as_view(), name="event_remove_host"),

	url(r"^(?P<event_id>[0-9]+)/show_attendees/$", ShowAttendees.as_view(), name="event_show_attendees"),
	url(r"^(?P<event_id>[0-9]+)/attendee/add/(?P<person_type>client|contact)/(?P<person_id>[0-9]+)/$", AttendeeAdd.as_view(), name="event_add_attendee"),
	url(r"^(?P<event_id>[0-9]+)/attendee/remove/(?P<attendee_id>[0-9]+)/$", AttendeeRemove.as_view(), name="event_remove_attendee"),

	url(r"^create/$", user_authenticated(EditEvent.as_view(template_name='events/create_event.html')), name="create_event"),
	url(r"^list/$", user_authenticated(ListEvents.as_view()), name="list_events"),
	url(r"^history/$", user_authenticated(ListEvents.as_view(history=True)), name="events_history"),
)
