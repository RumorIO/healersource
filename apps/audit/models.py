import json

from datetime import time, datetime
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.conf import settings
from django.contrib.auth.models import User
from healers.models import Appointment, HealerTimeslot


def human_time(minutes):
	h, m = divmod(minutes, 60)
	return time(h, m).strftime("%I:%M %p")


def human_exceptions(exceptions):
	return [
		datetime.utcfromtimestamp(ex).date().isoformat()
		for ex in exceptions]


def compare(obj1, obj2, excluded_keys):
	"""
	Compares two model instances for changed fields,
	exclude fields from excluded_keys param and private fields
	"""
	d1, d2 = obj1.__dict__, obj2.__dict__
	old, new = {}, {}
	for k, v in d1.items():
		if k in excluded_keys or k.startswith('_'):
			continue
		try:
			if v != d2[k]:
				old.update({k: v})
				new.update({k: d2[k]})
		except KeyError:
			old.update({k: v})

	return old, new


def audit_callback(sender, **kwargs):
	"""
	Save before and after state for timeslot
	"""
	instance = kwargs['instance']

	model_class = sender
	if model_class == Appointment:
		user = instance.last_modified_by
		audit_class = AppointmentAudit
		model_objects = Appointment.all_objects
	else:
		user = instance.healer.user
		audit_class = HealerTimeslotAudit
		model_objects = model_class.objects

	if 'delete' in kwargs:
		before_json = audit_class.timeslot_json(instance)
		after_json = 'deleted'
	else:
		before_instance = None
		if instance.pk:
			before_instance = model_objects.get(pk=instance.pk)
			before_json, after_json = audit_class.compare(before_instance, instance)
		else:
			before_json = 'created'
			after_json = audit_class.timeslot_json(instance)
	if before_json != after_json:
		audit_class.objects.create(
			timestamp=settings.GET_NOW(),
			timeslot=instance.pk if instance.pk else None,
			user=user,
			before=before_json,
			after=after_json
		)


def audit_delete_callback(sender, **kwargs):
	"""
	Save info about timeslot before delete
	"""
	kwargs['delete'] = True
	audit_callback(sender, **kwargs)


class TimeslotAudit(models.Model):
	"""
	Base class for timeslot audit
	"""
	timestamp = models.DateTimeField()
	user = models.ForeignKey(User)
	timeslot = models.PositiveIntegerField(blank=True, null=True)  # timeslot id
	before = models.TextField()
	after = models.TextField()
	excluded_keys = []  # list of keys to exclude from comparing

	@classmethod
	def compare(cls, before, after):
		"""
		Compares two timeslots, updates date, time, exceptions fields
		"""
		before_dict, after_dict = compare(before, after, cls.excluded_keys)

		if 'start_date' in before_dict:
			before_dict['start_date'] = before_dict['start_date'].isoformat()
			after_dict['start_date'] = after_dict['start_date'].isoformat()
		if 'end_date' in before_dict:
			if before_dict['end_date']:
				before_dict['end_date'] = before_dict['end_date'].isoformat()
			if after_dict['end_date']:
				after_dict['end_date'] = after_dict['end_date'].isoformat()
		if 'start_time' in before_dict:
			before_dict['start_time'] = human_time(before_dict['start_time'])
			after_dict['start_time'] = human_time(after_dict['start_time'])
		if 'end_time' in before_dict:
			before_dict['end_time'] = human_time(before_dict['end_time'])
			after_dict['end_time'] = human_time(after_dict['end_time'])
		if 'exceptions' in before_dict:
			before_dict['exceptions'] = human_exceptions(before_dict['exceptions'])
			after_dict['exceptions'] = human_exceptions(after_dict['exceptions'])

		return json.dumps(before_dict), json.dumps(after_dict)

	@classmethod
	def timeslot_json(cls, timeslot):
		ts_dict = timeslot.as_dict()

		ts_dict['start_time'] = human_time(ts_dict['start_time'])
		ts_dict['end_time'] = human_time(ts_dict['end_time'])
		ts_dict['exceptions'] = human_exceptions(timeslot.exceptions)

		return json.dumps(ts_dict)

	class Meta:
		abstract = True


class AppointmentAudit(TimeslotAudit):
	"""
	Log of changes for appointment
	"""
	excluded_keys = [
		'healer', 'client', 'created_by', 'created_date',
		'last_modified_by', 'last_modified_date']


class HealerTimeslotAudit(TimeslotAudit):
	"""
	Log of changes for healer timeslot
	"""
	excluded_keys = ['healer']


if settings.AUDIT_APPOINTMENTS:
	pre_save.connect(audit_callback, sender=Appointment)
	pre_delete.connect(audit_delete_callback, sender=Appointment)

if settings.AUDIT_AVAILABILITY:
	pre_save.connect(audit_callback, sender=HealerTimeslot)
	pre_delete.connect(audit_delete_callback, sender=HealerTimeslot)
