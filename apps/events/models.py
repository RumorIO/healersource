from datetime import datetime, date, time

from django.db.models.query_utils import Q
from django.db import models

from clients.models import Client, PersonAbstract
from healers.models import Healer, Location


class EventAttendee(PersonAbstract):
	pass


class EventLocationDate(models.Model):
	location = models.ForeignKey(Location)
	start = models.DateTimeField(default=datetime.combine(date.today(), time(12, 00)))
	end = models.DateTimeField(default=datetime.combine(date.today(), time(12, 00)))


class EventsManager(models.Manager):
	def get_queryset(self):
		return super(EventsManager, self).get_queryset()

	@classmethod
	def order(cls, qs, reversed=False):
		def remove_duplicates():
			result = []
			for record in qs:
				if record not in result:
					result.append(record)
			return result

		qs = qs.order_by('location_dates__start')
		if reversed:
			qs = qs.reverse()
		return remove_duplicates()

	def _initial_filter(self, client):
		qs = self.get_queryset()
		if client is not None:
			qs = qs.filter(client=client)
		return qs

	def current(self, client=None, ordered=True):
		"""Return curent events including events without date. Return ordered
		list of events if ordered = True else return unordered queryset."""
		qs = self._initial_filter(client)
		qs = qs.filter(Q(location_dates__end__gt=datetime.utcnow()) |
			Q(location_dates=None))
		if ordered:
			qs = self.order(qs)
		return qs

	def past(self, client=None):
		qs = self._initial_filter(client)
		qs = qs.filter(location_dates__end__lte=datetime.utcnow())
		return self.order(qs, True)


class EventType(models.Model):
	name = models.CharField(max_length=50)

	def __unicode__(self):
		return self.name


class Event(models.Model):
	client = models.ForeignKey(Client, related_name='events')
	title = models.CharField(max_length=1024)
	description = models.TextField()
	location_dates = models.ManyToManyField(EventLocationDate)
	type = models.ForeignKey(EventType)
	hosts = models.ManyToManyField(Healer)
	photo = models.ImageField(upload_to='event_photos', blank=True, null=True)
	attendees = models.ManyToManyField(EventAttendee)

	objects = EventsManager()

	def __unicode__(self):
		return self.title

	def is_past(self):
		return self.location_dates.filter(start__lte=datetime.utcnow()).exists()
