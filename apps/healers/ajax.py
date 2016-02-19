# -*- coding: utf8 -*-

#from apps.healers.ajax import UpdateOrCreateError

#from django.db.models.query_utils import Q
#from dajaxice.core import dajaxice_functions
#import logging
#log = logging.getLogger('dajaxice.DajaxiceRequest')
#log.info('1')
#from friends.importer import first_name, last_name
#from ajax_validation.views import form
#from ajax_validation.views import form
#from django.contrib.admin.views.decorators import username
#from ajax_validation.views import form
#from django.db.utils import error_msg
#from django.template.defaultfilters import escapejs

import functools
import json
import stripe
from datetime import datetime, timedelta, time

from emailconfirmation.models import EmailAddress, EmailConfirmation
from oauth_access.access import OAuthAccess, OAuth20Token, UserAssociation
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from dajax.core import Dajax
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from dajaxice.decorators import dajaxice_register
import autocomplete_hs
from contacts_hs.models import ContactInfo, ContactPhone, ContactEmail
from friends.models import Contact
from clients.models import (ClientPhoneNumber, create_dummy_user,
	ClientLocation, SiteJoinInvitation, Client)

from healers.forms import NewUserForm
from healers.models import (is_my_client, Healer, format_dates,
	HealerTimeslot, Appointment, UnavailableSlot, Vacation, Timeslot,
	TreatmentTypeLength, get_minutes, get_timestamp, Clients,
	AppointmentConflict, WellnessCenter, wcenter_get_provider,
	is_wellness_center, Room, TreatmentType, Location,
	is_wellness_center_location, WellnessCenterTreatmentTypeLength,
	DiscountCode, get_appointment_cost)
from healers.utils import (invite_or_create_client_friendship,
	get_wcenter_location_ids, get_available_healers,
	get_healer_wcenters_locations, check_room, has_treatments,
	get_healers_in_wcenter_with_schedule_editing_perm,
	wcenter_healer_has_treatment_types_, get_treatment_lengths_locations,
	get_tts_ttls_tbar_avail_ttls, get_timeslot_object,
	create_provider_availabilities_for_timeslot, get_locations)

from payments.stripe_connect import charge_for_appointment, create_card_token
from payments.utils import get_user_customer

TIMEFORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
stripe.api_version = settings.STRIPE_API_VERSION


def login_required_ajax(function):
	"""
	Decorator for views that checks that the user is logged in,
	sends dajax command to refresh page.
	"""

	@functools.wraps(function)
	def decorator(request, *args, **kwargs):
		if request.user.is_authenticated():
			return function(request, *args, **kwargs)
		else:
			dajax = Dajax()
			# dajax.script('location.reload();')
			return dajax.json()

	return decorator


def user_authenticated_ajax(function):
	"""
	Decorator for views that checks that the user is logged in,
	sends dajax command to refresh page.
	"""

	@functools.wraps(function)
	def decorator(request, *args, **kwargs):
		if request.user.is_authenticated() and request.user.is_active:
			return function(request, *args, **kwargs)
		elif request.user.is_authenticated() and not request.user.is_active:
			result = {
				'timeout_id': kwargs.get('timeout_id', 0),
				'confirm_email': True,
				'user_email': request.user.email
			}
			return json.dumps(result)
		else:
			dajax = Dajax()
			# dajax.script('location.reload();')
			return dajax.json()

	return decorator


class AjaxResult(object):

	def __init__(self, timeout_id):
		self.title = ''
		self.message = ''
		try:
			self.timeout_id = int(timeout_id)
		except Exception:
			self.timeout_id = 0
		self.slots = []
		self.action = ''
		self.intake_form_redirect = False

	def enable_intake_form_redirect(self):
		self.intake_form_redirect = True

	def success(self, message, title=None):
		self.message = message
		if title:
			self.title = title

	def error(self, message):
		self.message = message
		self.title = 'Error'

	def add_slot(self, slot, action, unavailable=0):
		slot_dict = slot.as_dict()
		slot_dict['unavailable'] = unavailable
		slot_dict['action'] = action
		self.slots.append(slot_dict)

	def dump(self):
		result = {'timeout_id': self.timeout_id,
		          'title': self.title,
		          'message': self.message,
		          'slots': self.slots,
		          'action': self.action,
		          'intake_form_redirect': self.intake_form_redirect}
		return json.dumps(result)

def prepare_dates(start, end, check_past=True, now=settings.GET_NOW(), check_diff_days=True):
	start_dt = convert_timestamp(start)
	end_dt = convert_timestamp(end)

	check_dates(start_dt, end_dt, check_past, now, check_diff_days)
	return start_dt, end_dt

def check_dates(start_dt, end_dt, check_past, now, check_diff_days=True):
	if end_dt<=start_dt:
		raise ValueError('End must be after start.')

	if check_diff_days:
		if start_dt.day!=end_dt.day and (end_dt.hour!=0 or end_dt.minute!=0):
			raise ValueError('Dates cannot be on different days.')

	if check_past:
		if start_dt.date() < now.date() or end_dt.date() < now.date():
			raise ValueError('Dates cannot be in the past.')


def convert_timestamp(timestamp):
	try:
		return datetime.utcfromtimestamp(timestamp/1000)
	except Exception:
		raise ValueError('Date in invalid format.')


@dajaxice_register(method='GET')
def getTimeslotsReadonly(request, healer, wcenter_id=None, treatment_type_id=None,
	only_my_locations=False):
	def get_treatment_type_locations():
		rooms = TreatmentType.objects.get(pk=treatment_type_id).rooms.all()
		if rooms.exists():
			return {room.location for room in rooms}
		else:
			wcenter_location_ids = get_wcenter_location_ids_from_wcenter_id(wcenter_id)
			return Location.objects.filter(pk__in=wcenter_location_ids)

	if isinstance(healer, basestring):
		try:
			healer = Healer.objects.get(user__username__iexact=healer)
		except (Healer.DoesNotExist, ValueError):
			return json.dumps('Could not find that healer')

		if not healer.is_schedule_visible(request.user):
			return json.dumps([])

	today = datetime.combine(healer.get_local_time(), time())
	start = today
	end = today + timedelta(days=healer.bookAheadDays) + timedelta(days=1)

	slots = HealerTimeslot.objects.filter(healer=healer).filter_by_datetime(start, end).order_by('start_date', 'start_time')
	appts = Appointment.objects.filter(healer=healer).filter_by_datetime(start, end).order_by('start_date', 'start_time')
	receiving_appts = Appointment.objects.filter(client=healer).filter_by_datetime(start, end).order_by('start_date', 'start_time')

	if only_my_locations:
		slots = slots.filter(location__in=healer.get_locations_objects())

	if wcenter_id is not None:
		locations = get_treatment_type_locations()
		slots = slots.filter(location__in=locations)
		appts = appts.filter(location__in=locations)
		receiving_appts = receiving_appts.filter(location__in=locations)

	unavailable_slots = UnavailableSlot.objects.filter(healer=healer).filter_by_datetime(start, end).order_by('start_date', 'start_time')
	vacations = Vacation.objects.filter(healer=healer).filter_by_datetime(start, end).order_by('start_date', 'start_time')
	vacations_by_date = []
	for vac in vacations:
		vacations_by_date.extend(vac.split_by_date())

	slotsList = [[a.start_date.isoformat(), a.start_time, a.end_time,
					a.end_date.isoformat() if a.end_date else (start.date()+timedelta(healer.bookAheadDays)).isoformat(),
					0, 1,
					-1,
					'',
					(a.repeat_period if a.repeat_period is not None else 0),
					(a.repeat_every if a.repeat_every else 0),
					(a.repeat_count if a.repeat_count is not None else 0),
					a.get_exceptions_dict(), 0,
					a.healer.setup_time] for a in appts]

	slotsList.extend([[v.start_date.isoformat(), v.start_time, v.end_time,
						v.end_date.isoformat() if v.end_date else (start.date() + timedelta(healer.bookAheadDays)).isoformat(),
						0, 1, -1, '', 0, 0, 0,
						v.get_exceptions_dict(), 1,
						v.healer.setup_time] for v in vacations_by_date])

	slotsList.extend([[s.start_date.isoformat(), s.start_time, s.end_time,
						s.end_date.isoformat() if s.end_date else s.start_date.isoformat(),
						0, 1, -1, '', 0, 0, 0,
						s.get_exceptions_dict(), 1,
						s.healer.setup_time] for s in unavailable_slots])

	slotsList.extend([[r.start_date.isoformat(), r.start_time, r.end_time,
						r.end_date.isoformat() if r.end_date else (start.date() + timedelta(healer.bookAheadDays)).isoformat(),
						0, 1, -1, '', 0, 0, 0,
						r.get_exceptions_dict(), 0,
						r.healer.setup_time] for r in receiving_appts])

	slotsList.extend([[s.start_date.isoformat(), s.start_time, s.end_time,
						s.end_date.isoformat() if s.end_date else (start.date()+timedelta(healer.bookAheadDays)).isoformat(),
						s.id, 0,
						s.location.id if s.location else -1,
						(str(s.location) if s.location is not None else 'Unspecified'),
						(s.repeat_period if s.repeat_period is not None else 0),
						(s.repeat_every if s.repeat_every else 0),
						0,
						s.get_exceptions_dict(), 0,
						s.healer.setup_time] for s in slots])

	keys = ['start_date', 'start_time', 'end_time', 'end_date', 'slot_id', 'unavailable', 'location', 'location_name',
			'repeat_period', 'repeat_every', 'repeat_count', 'exceptions', 'timeoff', 'setup_time']
	resultList = Timeslot.prepare_json_slots(keys, slotsList)

	return json.dumps(resultList)


@dajaxice_register
@user_authenticated_ajax
def getAppointments(request):
	try:
		healer = Healer.objects.get(user__id=request.user.id)
	except (Healer.DoesNotExist, ValueError):
		return json.dumps('Could not find healers %s' % (request.user.username))

	appts = Appointment.objects.get_active_json(healer)

	return json.dumps(appts)


def get_healer_object(request, username=None):
	if username is not None and username != '':
		if request.user.username != username:
			healer = wcenter_get_provider(request.user, username)
			if healer is None:
				return u"You don't have permission to edit the schedule"
			else:
				return healer
	try:
		return Healer.objects.get(user=request.user)
	except (Healer.DoesNotExist, ValueError):
		return u'Could not find healers %s' % (request.user.username)


def get_healer_generic(request, username, result):
	error = False
	healer = get_healer_object(request, username)
	if type(healer) is unicode:
		result.error(healer)
		error = True
		healer = result.dump()
	return healer, error


timeslot_keys = ['slot_id', 'start_date', 'start_time', 'end_time', 'end_date',
	'treatment_length', 'repeat_period', 'repeat_every', 'repeat_count',
	'exceptions', 'location', 'location_title', 'cost', 'room', 'room_name',
	'discount_code', 'client_id', 'client_name', 'client', 'note', 'unavailable',
	'client_has_email', 'timeoff', 'confirmed', 'hidden', 'setup_time',
	'healer_name', 'healer_username', 'intake', 'has_intake',
	'healer_has_notes_for_client', 'owner_healer_has_notes_for_client']


def get_now(healer):
	return datetime.combine(healer.get_local_time(), time())


def get_other_healers_appointments(current_healer, locations):
	appts_other_healers = Appointment.objects\
		.exclude(healer=current_healer)\
		.filter(location__in=locations)\
		.filter_by_datetime(get_now(current_healer))

	return [[a.id,
		a.start_date.isoformat(), a.start_time, a.end_time,
		a.end_date.isoformat() if a.end_date else 0,
		a.treatment_length.id if a.treatment_length else 0,
		a.repeat_period if a.repeat_period is not None else 0,
		a.repeat_every if a.repeat_every is not None else 0,
		a.repeat_count if a.repeat_count is not None else 0,
		a.get_exceptions_dict(),
		-1,
		'',
		'',
		a.room.id if a.room is not None else 0,
		a.room.name if a.room is not None else '',
		'',
		a.client.pk,
		'',
		a.client.user.username,
		unicode(a.note),
		4,
		1 if (a.client.user.email or ContactEmail.objects.get_first_email(a.client.user)) else 0,
		0,
		1 if a.confirmed else 0,
		1,
		a.healer.setup_time,
		a.healer.user.get_full_name(),
		a.healer.user.username,
		a.client_completed_form(),
		a.owner_healer_has_intake_form(),
		a.healer_has_notes_for_client(),
		a.owner_healer_has_notes_for_client(),
		] for a in appts_other_healers]


@dajaxice_register
@user_authenticated_ajax
def getCenterEditSchedule(request, username=None):
	"""Return data for wcenter schedule for selected healer."""
	def format_date(date):
		return date.strftime('%H:%M')

	def get_reload():
		return ((not wcenter_healer_has_treatment_types_(request.user, healer) and
				requesting_healer.username != healer.username) or not
					has_treatments(treatment_lengths, True, healer, requesting_healer))

	def get_treatment_lengths_locations_():
		locations = requesting_healer.get_locations()
		treatment_lengths_locations = get_treatment_lengths_locations(healer,
			locations, treatment_lengths)

		Location_Treatments = {}
		Treatments = {}
		Treatment_Types = {}
		for id, treatment_lengths_ in treatment_lengths_locations.items():
			Location_Treatments[id] = {}
			for length in treatment_lengths_:
				Location_Treatments[id][length.id] = json.loads(length.json_object())
				Treatments[length.id] = json.loads(length.json_object())
				Treatment_Types[length.id] = length.treatment_type.id
		return Location_Treatments, Treatments, Treatment_Types

	healer = get_healer_object(request, username)
	requesting_healer = get_object_or_404(Healer, user=request.user)
	treatment_lengths = TreatmentTypeLength.objects.filter(
		treatment_type__healer=requesting_healer)

	if get_reload():
		return json.dumps({'reload': True})

	Location_Treatments, Treatments, Treatment_Types = get_treatment_lengths_locations_()
	result = {
		'healer': {
			'Healer_Name': str(healer.user.client),
			'defaultTimeslotLength': healer.defaultTimeslotLength,
			'bookAheadDays': healer.bookAheadDays,
			'Office_Hours_Start': format_date(healer.office_hours_start),
			'Office_Hours_End': format_date(healer.office_hours_end),
		},
		'reload': False,
		'Location_Treatments': Location_Treatments,
		'Treatments': Treatments,
		'Treatment_Types': Treatment_Types,
	}

	return json.dumps(result)


@dajaxice_register
@user_authenticated_ajax
def getTimeslotsEdit(request, username=None):
	def get_slots(healer):
		return HealerTimeslot.objects.filter(healer=healer).filter_by_datetime(now)

	def get_appts(healer):
		return Appointment.objects.filter(healer=healer).filter_by_datetime(now)

	healer = get_healer_object(request, username)
	if type(healer) is unicode:
		return json.dumps(healer)
	now = get_now(healer)

	slots = get_slots(healer)
	appts = get_appts(healer)

	wellness_center = is_wellness_center(request.user)
	if wellness_center:
		locations = get_wcenter_location_ids(request.user)
		if request.user.username == username:
			healers = get_healers_in_wcenter_with_schedule_editing_perm(wellness_center)
			for healer in healers:
				slots = list(slots)
				appts = list(appts)
				# don't show availabilities of providers if common availability is enabled
				if not wellness_center.common_availability:
					slots += list(get_slots(healer).filter(location__in=locations))
				appts += list(get_appts(healer).filter(location__in=locations))
			slots_private = []
			appts_private = []
			otherHealersAppointments = []
		else:
			slots_private = slots.exclude(location__in=locations)
			appts_private = appts.exclude(location__in=locations)
			# don't show availabilities of providers if common availability is enabled
			if not wellness_center.common_availability:
				slots = slots.filter(location__in=locations)
			appts = appts.filter(location__in=locations)
	else:
		locations = get_healer_wcenters_locations(healer)

	if not (wellness_center and request.user.username == username):
		# hidden appointment list to check for room conflicts
		otherHealersAppointments = get_other_healers_appointments(healer, locations)

	slotsList = [[s.id,
					s.start_date.isoformat(), s.start_time, s.end_time,
					s.end_date.isoformat() if s.end_date else 0,
					0,
					s.repeat_period if s.repeat_period is not None else 0,
					s.repeat_every if s.repeat_every is not None else 0,
					0,
					s.get_exceptions_dict(),
					(s.location.id if s.location is not None else -1),
					(s.location.title if s.location is not None else ''),
					'',
					0,  # room id
					'',
					'',
					'',
					'',
					'',
					'',
					0,
					0,
					0,
					0,
					0,
					s.healer.setup_time,
					s.healer.user.get_full_name(),
					s.healer.user.username,
					False,
					False,
					False,
					False] for s in slots]

	apptsList = [[a.id,
					a.start_date.isoformat(), a.start_time, a.end_time,
					a.end_date.isoformat() if a.end_date else 0,
					a.treatment_length.id if a.treatment_length else 0,
					a.repeat_period if a.repeat_period is not None else 0,
					a.repeat_every if a.repeat_every is not None else 0,
					a.repeat_count if a.repeat_count is not None else 0,
					a.get_exceptions_dict(),
					a.location.id if a.location is not None else -1,
					a.location.title if a.location is not None else '',
					a.cost(),
					a.room.id if a.room is not None else 0,
					a.room.name if a.room is not None else '',
					a.discount_code.pk if a.discount_code is not None else '',
					a.client.pk,
					unicode(a.client),
					str(a.client.user.username),
					unicode(a.note),
					1,
					1 if (a.client.user.email or ContactEmail.objects.get_first_email(a.client.user)) else 0,
					0,
					1 if a.confirmed else 0,
					0,
					a.healer.setup_time,
					a.healer.user.get_full_name(),
					a.healer.user.username,
					a.client_completed_form(),
					a.owner_healer_has_intake_form(),
					a.healer_has_notes_for_client(),
					a.owner_healer_has_notes_for_client()] for a in appts]

	if wellness_center:  # special list of availability and appointments to display private appointments in grey without details.
		slotsList += [[s.id,
						s.start_date.isoformat(), s.start_time, s.end_time,
						s.end_date.isoformat() if s.end_date else 0,
						0,
						s.repeat_period if s.repeat_period is not None else 0,
						s.repeat_every if s.repeat_every is not None else 0,
						0,
						s.get_exceptions_dict(),
						-1,
						'',
						'',
						0,   # room_id
						'',  # room_name
						'',
						'',
						'Weekly', '', '',
						3,
						0,
						0,
						0,
						1,
						s.healer.setup_time,
						s.healer.user.get_full_name(),
						s.healer.user.username, False, False, False, False] for s in slots_private]

		apptsList += [[a.id,
						a.start_date.isoformat(), a.start_time, a.end_time,
						a.end_date.isoformat() if a.end_date else 0,
						a.treatment_length.id if a.treatment_length else 0,
						a.repeat_period if a.repeat_period is not None else 0,
						a.repeat_every if a.repeat_every is not None else 0,
						a.repeat_count if a.repeat_count is not None else 0,
						a.get_exceptions_dict(),
						-1,
						'',
						'',
						a.room.id if a.room is not None else 0,
						a.room.name if a.room is not None else '',
						a.discount_code.pk if a.discount_code is not None else '',
						a.client.pk,
						'',
						a.client.user.username,
						unicode(a.note),
						2,
						1 if (a.client.user.email or ContactEmail.objects.get_first_email(a.client.user)) else 0,
						0,
						1 if a.confirmed else 0,
						1,
						a.healer.setup_time,
						a.healer.user.get_full_name(),
						a.healer.user.username,
						a.client_completed_form(),
						a.owner_healer_has_intake_form(),
						a.healer_has_notes_for_client(),
						a.owner_healer_has_notes_for_client()] for a in appts_private]

	vacations = Vacation.objects.filter(healer__id=healer.id).filter_by_datetime(now).order_by('start_date', 'start_time')
	offList = [[v.id,
				v.start_date.isoformat(), v.start_time, v.end_time,
				v.end_date.isoformat() if v.end_date else 0,
				0,
				0,
				0,
				0,
				[],
				-1,
				'',
				'',
				0,   # room_id
				'',  # room_name
				'',
				'',
				'',
				'',
				'',
				1,
				0,
				1,
				0,
				0,
				v.healer.setup_time,
				v.healer.user.get_full_name(),
				v.healer.user.username, False, False, False, False] for v in vacations]

	resultList = Timeslot.prepare_json_slots(timeslot_keys, slotsList + apptsList + otherHealersAppointments + offList)
	return json.dumps(resultList)


def get_rooms(treatment_type, location_ids):
	def get_treatment_rooms():
		treatment_rooms = treatment_type.rooms.all()
		if treatment_rooms.exists():
			return treatment_rooms

	treatment_rooms = get_treatment_rooms()
	if treatment_rooms is not None:
		return treatment_rooms
	else:
		return Room.objects.filter(location__in=location_ids)


def check_schedule_permission(healer, location=None, location_id=None):
	""" Check if healer has permission to use center location.

	Return error (str) if there is no permission and None otherwise.
	"""
	if location_id is None:
		if location is not None:
			location_id = location.id
		else:
			return
	if (is_wellness_center_location(location_id) and
			not is_wellness_center(healer)):
		if not healer.user.has_perm(Healer.SCHEDULE_PERMISSION):
			if healer.user.is_active:
				return "Practitioner doesn't have permission to book appointments at the chosen location."
			else:
				return "Cannot create appointment because %s hasn't logged in yet." % healer


def get_treatment_length(treatment_length_id, healer, result):
	try:
		treatment_length_id = int(treatment_length_id)
		return TreatmentTypeLength.objects.get(id=treatment_length_id,
			treatment_type__in=healer.get_all_treatment_types())
	except (ValueError, TypeError):
		result.error('Treatment type id in invalid format.')
		return result.dump()
	except TreatmentTypeLength.DoesNotExist:
		result.error('Could not find that Treatment Type.')
		return result.dump()


def get_discount_code(discount_code, healer, result):
	if discount_code:
		try:
			return DiscountCode.objects.get(healer=healer, code__iexact=discount_code)
		except DiscountCode.DoesNotExist:
			result.error('Invalid Discount Code - Please Try Again.')
			return result.dump()


def create_appointment_for_timeslot(request, timeslot, start, treatment_length,
									client, note, discount_code, timeout_id,
									check_for_conflicts=False, charge_data=None):
	def get_room():
		def prioritize_rooms(room1, room2):
			def get_room_weight(room):
				treatment_types = room.treatment_types.filter(is_deleted=False)
				if treatment_types.exists():
					return treatment_types.count()
				else:
					return 999  # max number to prioritize all purpose rooms
			return get_room_weight(room2) - get_room_weight(room1)

		if location_id is not None:
			if is_wellness_center_location(location_id):
				rooms = get_rooms(treatment_length.treatment_type, [location_id])
				rooms = sorted(rooms, prioritize_rooms)
				for room in rooms:
					# just checks for conflicts
					if Appointment.create_new(room_id=room.id, check_for_conflicts=True, **appt_data):
						return room.id

	result = AjaxResult(timeout_id)

	try:
		start_dt = convert_timestamp(start)
	except ValueError as e:
		result.error(str(e))
		return result.dump()
	timeslot = get_timeslot_object(timeslot, result)
	if type(timeslot) != HealerTimeslot:
		return timeslot

	timeslot_user = timeslot.healer.user
	try:
		client = int(client)
		client = Client.objects.get(id=client)
	except (ValueError, TypeError):
		result.error('Client id in invalid format.')
		return result.dump()
	except Client.DoesNotExist:
		result.error('Could not find that Client.')
		return result.dump()

	if request.user.id and request.user.id != client.user.id:
		result.error('Wrong client.')
		return result.dump()

	treatment_length = get_treatment_length(treatment_length, timeslot.healer, result)
	if type(treatment_length) != TreatmentTypeLength:
		return treatment_length

	discount_code = get_discount_code(discount_code, treatment_length.treatment_type.healer, result)
	if discount_code is not None and type(discount_code) != DiscountCode:
		return discount_code

	end_dt = start_dt + timedelta(minutes=treatment_length.length)
	if get_minutes(start_dt) < timeslot.start_time or get_minutes(end_dt) > timeslot.end_time:
		result.error('Invalid start date.')
		return result.dump()

	healer_local_time = timeslot.healer.get_local_time()
	if start_dt < (healer_local_time + timedelta(hours=timeslot.healer.leadTime)):
		result.error('<p>%s requires a minimum of %d hours advance notice.</p>'
			'<p>Your Appointment was not scheduled.</p>' % (str(timeslot.healer), int(timeslot.healer.leadTime)))
		return result.dump()

	if start_dt.date() > (healer_local_time.date() + timedelta(days=timeslot.healer.bookAheadDays)):
		result.error("You can't book more than %s days ahead" % timeslot.healer.bookAheadDays)
		return result.dump()

	#   try:
	#	   appt = Appointment.objects.get(healer=timeslot.healer,
	#									  start_date=start_dt.date(),
	#									  end_date=start_dt.date(),
	#									  start_time=get_minutes(start_dt),
	#									  end_time=get_minutes(end_dt),
	#									  location=timeslot.location)
	#   except ObjectDoesNotExist:
	location_id = timeslot.location.id if timeslot.location else None
	schedule_permission_result = check_schedule_permission(timeslot.healer,
		location_id=location_id)
	if schedule_permission_result is not None:
		result.error(schedule_permission_result)
		return result.dump()

	appt_data = {
		'healer_user_id': timeslot.healer.user.id,
		'client_id': client.id,
		'location_id': location_id,
		'start': start_dt,
		'end': end_dt,
		'creator_user': request.user,
		'treatment_length': treatment_length,
		'note': note,
		'creator': client.user,
		'discount_code': discount_code,
	}

	if check_for_conflicts:
		return Appointment.create_new(room_id=get_room(),
			check_for_conflicts=True, **appt_data)

	appt, result_code, exceptions, available_dates = Appointment.create_new(
		room_id=get_room(), **appt_data)
	#   appt = results[0]

	if result_code == 4:
		result.error(appt)
		return result.dump()
	elif result_code != 0:
		result.error('Sadly, this time is no longer available. Please Try Again!')
		return result.dump()

	if timeslot_user != client.user:
		if location_id is None:
			location_user = timeslot_user
		else:
			location_user = ClientLocation.objects.get(location=location_id).client.user
		if location_user == timeslot_user:
			invite_or_create_client_friendship(client.user, timeslot_user)
		else:
			if wcenter_get_provider(location_user, timeslot_user.username):
				invite_or_create_client_friendship(client.user, location_user)

	if not (charge_data is None or treatment_length.treatment_type.healer.is_card_required()):
		charge_data['appointment'] = appt
		charge_result = charge_for_appointment(**charge_data)
		if charge_result is not None:
			appt.delete()
			result.error(charge_result['error'])
			return result.dump()

	if appt.confirmed:
		result.success('Your Appointment is confirmed, see you soon!', 'Appointment Scheduled')

	#   elif not client.has_confirmed_email():
	#	   request_text = 'request ' if timeslot.healer.manualAppointmentConfirmation != Healer.CONFIRM_AUTO else ''
	#	   result.success('<p>Thanks for booking!</p>'
	#					  '<p><em>To verify your identity, you must register with HealerSource before your appointment %sis sent to %s</em></p>'
	#					  '<p><strong>* Please check your email and click on the registration link *</strong></p> ' %
	#					  (request_text, appt.healer.user.client), 'Appointment Scheduled')
	else:
		result.success('<p>Thanks for booking!</p>'
			'<p style="color:blue;"><em>Your Appointment has been requested, but is not yet confirmed.</em></p>'
			'<p><strong>You will receive an email when %s confirms or declines it.</strong></p>' %
			appt.healer.user.client, 'Appointment Requested')

	if (timeslot.healer.intakeFormBooking == Healer.INTAKE_FORM_PROMPT and
			timeslot.healer.has_intake_form() and
			is_my_client(timeslot.healer.user, client.user)):
		result.enable_intake_form_redirect()
	elif timeslot.healer.intakeFormBooking == Healer.INTAKE_FORM_EMAIL:
		timeslot.healer.send_intake_form(appt.healer.user.client)
	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def timeslot_book(request, timeslot, start, treatment_length, client, note,
					discount_code, timeout_id, check_for_conflicts=False,
					card_token=None, save_card=False, skip_charge=False):
	"""Book timeslot. Check for conflicts is used only for stripe connect charges
	to check if appointment can be created before charging and also checks if
	cost can be casted into float and if it's > 0. Also returns description and
	amount and the has_card boolean"""

	def get_amount():
		cost = get_appointment_cost(tlength, discount_code)
		if type(cost) == float and cost > 0:
			return cost
			#return round(cost * tlength_healer.deposit_percentage / 100.0, 2)
		else:
			return 0

	result = AjaxResult(timeout_id)

	timeslot_object = get_timeslot_object(timeslot, result)
	if type(timeslot_object) != HealerTimeslot:
		return timeslot_object

	tslot_healer = timeslot_object.healer
	tlength = get_treatment_length(treatment_length, tslot_healer, result)
	if type(tlength) != TreatmentTypeLength:
		return tlength

	treatment_type = tlength.treatment_type
	tlength_healer = treatment_type.healer

	discount_code = get_discount_code(discount_code, tlength_healer, result)
	if discount_code is not None and type(discount_code) != DiscountCode:
		return discount_code

	charge_data = None
	if tlength_healer.is_payment_or_card_required():
		amount = get_amount()
		if not (skip_charge and amount == 0):
			customer = get_user_customer(request.user)
			healer_user = tlength_healer.user
			has_card = customer.can_charge()
			if check_for_conflicts:
				no_conflicts = create_appointment_for_timeslot(request, timeslot,
						start, treatment_length, client, note, discount_code, timeout_id, True)
				result = {
					'timeout_id': int(timeout_id),
					'no_conflicts': no_conflicts,
					'amount': amount,
					'description': unicode(treatment_type),
					'has_card': has_card,
					'card_autosave': tlength_healer.is_card_required()}
				return json.dumps(result)
			if save_card:
				try:
					customer.update_card(card_token)
					has_card = True
				except stripe.CardError, e:
					result.error(e.message)
					return result.dump()
			if has_card:
				card_token = create_card_token(customer, healer_user)
			if card_token is not None:
				charge_data = {
					'card_token': card_token,
					'amount': amount,
				}
			else:
				result.error('Incorrect Card')
				return result.dump()

	return create_appointment_for_timeslot(request, timeslot, start,
		treatment_length, client, note, discount_code, timeout_id, charge_data=charge_data)


def timeslot_save(timeslot):
	updated_slots = []
	conflict_weekly_msg = """<p>This would conflict with another Weekly Availability.
		Try adding a One-Time Availability instead.</p><p><b>Your changes were not saved.</b></p>"""
	result_code, exceptions, conflicting_slots = timeslot.find_conflicts(HealerTimeslot.objects.filter(
		healer=timeslot.healer, location=timeslot.location))
	if result_code in [0, 2]:
		if not timeslot.is_single():
			for slot in conflicting_slots:
				if not slot.is_single():
					return conflict_weekly_msg, updated_slots

			timeslot.exceptions.extend(exceptions)
	elif result_code == 3:
		for slot in conflicting_slots:
			if slot.is_single():
				return '<p>This would conflict with another One-Time Availability.</p><p><b>Your changes were not saved.</b></p>', updated_slots

		# for repeating slots silently add exception
		for slot in conflicting_slots:
			if not slot.is_single():
				slot.exceptions.append(get_timestamp(timeslot.start_date))
				slot.save()
				updated_slots.append(slot)
	else:
		return conflict_weekly_msg, updated_slots
	timeslot.save()
	return None, updated_slots


@dajaxice_register
@user_authenticated_ajax
def save_schedule_full_width(request, status):
	healer = get_object_or_404(Healer, user=request.user)
	healer.schedule_full_width = status
	healer.save()


@dajaxice_register
@user_authenticated_ajax
def save_first_week_day_setting(request, status):
	healer = get_object_or_404(Healer, user=request.user)
	healer.schedule_start_from_sunday_setting = status
	healer.save()


@dajaxice_register
@user_authenticated_ajax
def save_side_by_side_setting(request, status):
	wc = get_object_or_404(WellnessCenter, user=request.user)
	wc.schedule_side_by_side_setting = status
	wc.save()


@dajaxice_register
@user_authenticated_ajax
def save_schedule_dropdown_provider_list(request, status):
	wc = get_object_or_404(WellnessCenter, user=request.user)
	wc.schedule_dropdown_provider_list = status
	wc.save()


@dajaxice_register
@user_authenticated_ajax
def timeslot_new(request, start, end, end_date, location_id, weekly, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	if type(weekly) != bool:
		result.error('Weekly in invalid format.')
		return result.dump()

	try:
		start_dt, end_dt = prepare_dates(start, end, check_past=False)
		if end_date:
			end_date = convert_timestamp(end_date).date()
			if end_date < start_dt.date():
				raise ValueError('End must be after start.')
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	healer, error = get_healer_generic(request, username, result)

	if error:
		return healer
	try:
		location_id = int(location_id)

		schedule_permission_result = check_schedule_permission(healer,
			location_id=location_id)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

		healer_location = ClientLocation.objects.filter(client__user__id=request.user.id).order_by('-location__is_default')
		if location_id:
			healer_location = healer_location.filter(location__id=location_id)
		location = healer_location[0].location
	except IndexError:
		wcenter_location = healer.get_wellness_center_locations(location_id)
		if wcenter_location:
			location = wcenter_location[0].location
		else:
			location = None
	except (ValueError, TypeError):
		location = None

	if location is None and username is not None and username != request.user.username:
		result.error("You don't have permission to add availability for this location.")
		return result.dump()

	if not healer.healer_treatment_types.filter(is_deleted=False).exists():
		result.error('You must add at least one Treatment Type before adding Availability. <a href="%s">Click here</a>.' % reverse('treatment_types'))
		return result.dump()

	timeslot = HealerTimeslot(healer=healer, location=location)
	timeslot.set_dates(start_dt, end_dt)
	timeslot.set_weekly(weekly, end_date)
	error, updated_slots = timeslot_save(timeslot)
	if error:
		result.error(error)
		return result.dump()
	for slot in updated_slots:
		result.add_slot(slot, 'update')

	result.add_slot(timeslot, 'new')
	center = is_wellness_center(healer)
	if center and center.common_availability:
		create_provider_availabilities_for_timeslot(center, timeslot)
	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def timeslot_update(request, timeslot_id,
					start_old, end_old, start_new, end_new,
					start_date, end_date, weekly_new, all_slots, timeout_id, username=None):

	result = AjaxResult(timeout_id)
	try:
		# calculate delta for weekly slots
		start_old_dt, end_old_dt = prepare_dates(start_old, end_old, check_past=False)
		start_new_dt, end_new_dt = prepare_dates(start_new, end_new, check_past=False)
		start_delta = start_new_dt - start_old_dt
		end_delta = end_new_dt - end_old_dt
		if start_date:
			start_date = convert_timestamp(start_date).date()
		if end_date:
			end_date = convert_timestamp(end_date).date()
			if end_date < start_new_dt.date() or (start_date and end_date < start_date):
				raise ValueError('End must be after start.')
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	all_slots = bool(all_slots)
	weekly_new = bool(weekly_new)

	try:
		timeslot_id = int(timeslot_id)
		timeslot = HealerTimeslot.objects.get(healer=healer, id=timeslot_id)
		schedule_permission_result = check_schedule_permission(healer,
			location=timeslot.location)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

	except (HealerTimeslot.DoesNotExist, ValueError):
		result.error('Could not find timeslot<br />%s<br />%s' % (healer.user.username, timeslot_id))
		return result.dump()

	if all_slots or timeslot.is_single():
		new_start = start_new_dt if not weekly_new else (timeslot.start + start_delta)
		new_end = end_new_dt if not weekly_new else (timeslot.end + end_delta)
		if timeslot.repeat_period:
			timeslot.shift_exceptions(start_old_dt.date(), start_new_dt.date())
		timeslot.set_dates(new_start, new_end)
		timeslot.set_weekly(weekly_new, end_date)
		if start_date:
			timeslot.start_date = start_date
		error, updated_slots = timeslot_save(timeslot)
		if error:
			result.error(error)
			return result.dump()
		for slot in updated_slots:
			result.add_slot(slot, 'update')
		result.add_slot(timeslot, 'update')
	else:
		single_timeslot, timeslot = timeslot.convert_to_single(start_old_dt, start_new_dt, end_new_dt)
		result.add_slot(single_timeslot, 'new')
		result.add_slot(timeslot, 'update')

	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def timeslot_delete(request, timeslot_id, start, all_slots, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	try:
		start_dt = convert_timestamp(start)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	all_slots = bool(all_slots)

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	try:
		timeslot_id = int(timeslot_id)
		timeslot = HealerTimeslot.objects.get(healer=healer, id=timeslot_id)
		schedule_permission_result = check_schedule_permission(healer,
			location=timeslot.location)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

	except (HealerTimeslot.DoesNotExist, ValueError):
		result.error('Could not find timeslot<br />%s<br />%s' % (healer.user.username, timeslot_id))
		return result.dump()

	if all_slots or not timeslot.repeat_period:
		result.add_slot(timeslot, 'delete')
		timeslot.delete()
	else:
		timeslot.delete_single(start_dt)
		result.add_slot(timeslot, 'update')

	return result.dump()

@dajaxice_register
@user_authenticated_ajax
def timeslot_delete_future(request, timeslot_id, start, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	try:
		start_dt = convert_timestamp(start)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	try:
		timeslot_id = int(timeslot_id)
		timeslot = HealerTimeslot.objects.get(healer=healer, id=timeslot_id)
		if timeslot.is_single():
			return result.dump()
	except (HealerTimeslot.DoesNotExist, ValueError):
		result.error('Could not find timeslot<br />%s<br />%s' % (healer.user.username, timeslot_id))
		return result.dump()

	if timeslot.start_date == start_dt.date():
		result.add_slot(timeslot, 'delete')
		timeslot.delete()
	else:
		timeslot.end_date = start_dt.date() - timedelta(weeks=1)
		if timeslot.start_date == timeslot.end_date:
			timeslot.repeat_period = None
		timeslot.save()
		result.add_slot(timeslot, 'update')

	return result.dump()

#def createNewSlot(slots, appts, day, start, end, healers, weekly=True):
#   start = datetime(day.year, day.month, day.day, start.hour, start.minute, 0)
#   end = datetime(day.year, day.month, day.day, end.hour, end.minute, 0)
#
#   slotConflict = is_conflict(slots, start, end)
#   apptConflict = is_conflict(appts, start, end)
#   if ((not slotConflict) and (not apptConflict)):
#	   timeslot_new = HealerTimeslot(healers=healers, start=start, end=end, weekly=weekly)
#	   timeslot_new.save()


def client_check(result, healer, client_id, client_type):
	try:
		client_id = int(client_id)
	except (ValueError, TypeError):
		result.error('Client id in invalid format.')
		return result

	if client_type == 'contact':
		try:
			contact = Contact.objects.get(id=client_id)
			try:
				user = contact.users.all()[0]
			except IndexError:
				user = None
				if contact.email:
					try:
						user = User.objects.filter(email=contact.email)[0]
					except IndexError:
						pass
				if not user:
					names = contact.name.split(' ', 1)
					first_name = names[0].strip()
					try:
						last_name = names[1].strip()
					except IndexError:
						last_name = ''
					user = create_dummy_user(first_name, last_name, contact.email)
				contact.users.add(user)
			try:
				client = Client.objects.get(user=user)
			except Client.DoesNotExist:
				client = Client.objects.create(user=user, approval_rating=100)
				if contact.email:
					SiteJoinInvitation.objects.send_invitation(healer.user, contact.email, '', is_to_healer=False)
			if not is_my_client(healer.user, user):
				friendship = Clients(from_user=healer.user, to_user=user)
				friendship.save()
			return client.id
		except Contact.DoesNotExist:
			result.error('Could not find that contact.')
			return result
	else:
		try:
			client = Client.objects.get(id=client_id)
		except Client.DoesNotExist:
			result.error('Could not find that client.')
			return result


@dajaxice_register
@user_authenticated_ajax
def appointment_new(request, client_id, client_type, start, end, location, treatment_length,
					repeat_period, repeat_every, repeat_count, conflict_solving,
					note, timeout_id, notify_client=True, username=None, room_id=None, discount_code=None):

	result = AjaxResult(timeout_id)
	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer
	try:
		start_dt, end_dt = prepare_dates(start, end, now=healer.get_local_time())
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	try:
		conflict_solving = int(conflict_solving)
	except (ValueError, TypeError):
		result.error('Conflict solving code in invalid format.')
		return result.dump()


	client_check_result = client_check(result, healer, client_id, client_type)
	if client_check_result is not None:
		if type(client_check_result) == type(result): # on error
			return client_check_result.dump()
		else:
			client_id = client_check_result

	try:
		location = int(location)
		ClientLocation.objects.get(client=healer, location__id=location)
	except ClientLocation.DoesNotExist:
		if not healer.get_wellness_center_locations(location):
			location = None
	except ValueError:
		result.error('Location id in invalid format.')
		return result.dump()
	except TypeError:
		location = None

	schedule_permission_result = check_schedule_permission(healer,
		location_id=location)
	if schedule_permission_result is not None:
		result.error(schedule_permission_result)
		return result.dump()

	try:
		treatment_length = int(treatment_length)
	except ValueError:
		result.error('Treatment length id in invalid format.')
		return result.dump()
	if treatment_length > 0:
		try:
			treatment_length = TreatmentTypeLength.objects.get(
				id=treatment_length, treatment_type__in=healer.get_all_treatment_types())
		except Exception:
			result.error('Could not find treatment type.')
			return result.dump()
	else:
		treatment_length = None

	# Check discount code
	if discount_code:
		try:
			is_wcenter = is_wellness_center(request.user)
			if is_wcenter:
				discount_code_healer = is_wcenter
			else:
				discount_code_healer = healer
			discount_code = DiscountCode.objects.get(healer=discount_code_healer, pk=discount_code)
		except DiscountCode.DoesNotExist:
			result.error('Invalid Discount Code - Please Try Again.')
			return result.dump()
	else:
		discount_code = None

	try:
		if repeat_period:
			repeat_period = int(repeat_period)
			if repeat_period not in zip(*Timeslot.REPEAT_CHOICES)[0]:
				raise ValueError()
		if repeat_every:
			repeat_every = int(repeat_every)
		if repeat_count:
			repeat_count = int(repeat_count)
	except ValueError:
		result.error('Recurrency options in invalid format.')
		return result.dump()

	def user_can_edit_schedule():
		return request.user == healer.user or wcenter_get_provider(request.user, healer.user.username)

	if healer.scheduleVisibility == Healer.VISIBLE_DISABLED and not user_can_edit_schedule():
		result.error('This Provider no longer accepts online bookings')
		return result.dump()

	appt, result_code, exceptions, available_dates = Appointment.create_new(
		healer_user_id=healer.user.id,
		client_id=client_id,
		location_id=location,
		room_id=room_id,
		start=start_dt, end=end_dt,
		creator_user=request.user,
		treatment_length=treatment_length,
		repeat_period=repeat_period,
		repeat_every=repeat_every,
		repeat_count=repeat_count,
		conflict_solving=conflict_solving,
		note=note,
		notify_client=notify_client,
		creator=request.user,
		discount_code=discount_code)

	if result_code==1:
		exception_dt = datetime.utcfromtimestamp(exceptions[0])
		conflict_date = format_dates([exception_dt])[0]
		result.error(('<p>There was a conflict with another repeating appointment on %s.</p>'
		              '<p> Your changes were not saved.</p>') % conflict_date)
		return result.dump()
	elif result_code==2:
		dajax = Dajax()
		dajax.script("dlg_appt_reschedule_conflict_solving(%s, %s, %s , 'client', %s)" % (appt.json_object(),
		                                                                                  format_dates([datetime.utcfromtimestamp(ex) for ex in exceptions]),
		                                                                                  format_dates(available_dates) if available_dates else [],
		                                                                                  timeout_id))
		return dajax.json()
	elif result_code==3:
		result.error('This conflicts with another appointment.')
		return result.dump()
	elif result_code==4:
		result.error(appt)
		return result.dump()

	if Vacation.check_for_conflicts(appt):
		result.add_slot(appt, 'new', unavailable=1)
		result.success('You have scheduled this appointment during your time off. '
		               'Remember to take care of yourself too!')
		return result.dump()

	#   healer.save_send_notification(notify_client)

	result.add_slot(appt, 'new', unavailable=1)
	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def appointment_update(request, appointment, start_old, end_old, start_new,
	end_new, treatment_length, location_new, note, conflict_solving, all_slots,
	timeout_id, notify_client=True, username=None, client_id=None,
	client_type=None, room_id=None, discount_code=None):
	result = AjaxResult(timeout_id)

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	try:
		appointment = int(appointment)
		appt = Appointment.objects.get(healer=healer, id=appointment)

		schedule_permission_result = check_schedule_permission(healer,
			location=appt.location)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

	except (ValueError, TypeError):
		result.error('Appointment id in invalid format.')
		return result.dump()
	except Appointment.DoesNotExist:
		result.error('Could not find appointment: %s' % appointment)
		return result.dump()

	try:
		start_old_dt, end_old_dt = prepare_dates(start_old, end_old, now=healer.get_local_time())
		start_new_dt, end_new_dt = prepare_dates(start_new, end_new, now=healer.get_local_time())
		start_delta = start_new_dt - start_old_dt
		end_delta = end_new_dt - end_old_dt
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	if type(all_slots) != bool:
		result.error('All slots flag in invalid format.')
		return result.dump()

	if all_slots and not appt.check_first_instance_dates(start_delta, end_delta):
		result.error('Dates of first appointment cannot be in the past.')
		return result.dump()

	if client_id is not None:
		client_check_result = client_check(result, healer, client_id, client_type)
		if client_check_result is not None:
			if type(client_check_result) == type(result): # on error
				return client_check_result.dump()
			else:
				client_id = client_check_result
		client = Client.objects.get(pk=client_id)
	else:
		client = None

	try:
		location_new = int(location_new)
		location = ClientLocation.objects.get(client=healer, location__id=location_new).location
	except ClientLocation.DoesNotExist:
		wcenter_location = healer.get_wellness_center_locations(location_new)
		if wcenter_location:
			location = wcenter_location[0].location
		else:
			location = None
	except ValueError:
		result.error('Location id in invalid format.')
		return result.dump()
	except TypeError:
		location = None

	try:
		treatment_length = int(treatment_length)
	except ValueError:
		result.error('Treatment length id in invalid format.')
		return result.dump()
	if treatment_length > 0:
		try:
			treatment_length = TreatmentTypeLength.objects.get(
				id=treatment_length, treatment_type__in=healer.get_all_treatment_types())
		except Exception:
			result.error('Could not find treatment type.')
			return result.dump()
	else:
		treatment_length = None

	is_wcenter = is_wellness_center(request.user)

	# Check discount code
	if discount_code:
		try:
			if is_wcenter:
				discount_code_healer = is_wcenter
			else:
				discount_code_healer = healer
			discount_code = DiscountCode.objects.get(healer=discount_code_healer, pk=discount_code)
		except DiscountCode.DoesNotExist:
			result.error('Invalid Discount Code - Please Try Again.')
			return result.dump()
	else:
		discount_code = None

	if location is not None:
		try:
			room = check_room(room_id, location.id, treatment_length)
		except Exception as e:
			result.error(str(e))
			return result.dump()
	else:
		room = None

	if all_slots or appt.is_single():
		result_code, exceptions, available_dates = appt.update(start_delta,
			end_delta, treatment_length, location, room, note,
			conflict_solving, client, discount_code)
		if result_code == 0:
			if (appt.is_data_changed(start_delta, end_delta, treatment_length, location, discount_code) or client) and notify_client:
				if is_wcenter:
					notify_created_user = appt.client.user
				else:
					notify_created_user = healer.user
				appt.notify_updated(notify_created_user, {'start': start_old_dt, 'end': end_old_dt}, is_wcenter)

		if result_code == 1:
			exception_dt = datetime.utcfromtimestamp(exceptions[0])
			conflict_date = format_dates([exception_dt])[0]
			result.error(('<p>There was a conflict with another repeating appointment on %s.</p>'
			              '<p> Your changes were not saved.</p>') % conflict_date)
			return result.dump()
		elif result_code == 2:
			dajax = Dajax()
			dajax.script("dlg_appt_reschedule_conflict_solving(%s, %s, %s, '', %s, %s, %s, %s, %s)" %
			             (appt.json_object(),
			              format_dates([datetime.utcfromtimestamp(ex) for ex in exceptions]),
			              format_dates(available_dates) if available_dates else [],
			              timeout_id,
			              start_old, end_old, start_new, end_new))
			return dajax.json()
		elif result_code == 3:
			result.error('This conflicts with another appointment.')
			return result.dump()

		if Vacation.check_for_conflicts(appt):
			result.success('You have scheduled this appointment during your time off. '
			               'Remember to take care of yourself too!')
			return result.dump()

		result.add_slot(appt, 'update', unavailable=1)
	else:
		try:
			single_appt, appt = appt.convert_to_single(start_old_dt, start_new_dt, end_new_dt)
		except AppointmentConflict:
			result.error('This conflicts with another appointment.')
			return result.dump()
		single_appt.treatment_length = treatment_length
		single_appt.location = location
		single_appt.room = room
		single_appt.note = note
		single_appt.discount_code = discount_code
		if client is not None:
			single_appt.client = client
		single_appt.save()
		if (single_appt.is_data_changed(start_delta, end_delta, treatment_length, location, discount_code) or client) and notify_client:
			single_appt.notify_updated(healer.user, {'start': start_old_dt, 'end': end_old_dt}, is_wcenter)
		result.add_slot(appt, 'delete' if appt.canceled else 'update', unavailable=1)
		result.add_slot(single_appt, 'update', unavailable=1)

	#   request.user.client.healer.save_send_notification(notify_client)

	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def appointment_delete_future(request, appointment, start, timeout_id, notify_client=True, username=None):
	"""
	Delete appointment recurrency after start
	"""
	result = AjaxResult(timeout_id)

	try:
		start_dt = convert_timestamp(start)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	try:
		appointment_id = int(appointment)
		appt = Appointment.objects.get(healer=healer, id=appointment_id)
		schedule_permission_result = check_schedule_permission(healer,
			location=appt.location)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

		if appt.is_single():
			return result.dump()
	except (Appointment.DoesNotExist, ValueError):
		result.error('Could not find appointment<br />%s<br />%s' % (healer.user.username, appointment))
		return result.dump()

	prev_dates = {'start': appt.start, 'end': appt.end}
	new_appt = appt.split_on_past(start_dt)
	appt.cancel(healer.user)

	if notify_client:
		appt.notify_updated(healer.user, prev_dates, is_wellness_center(request.user))

	if new_appt:
		result.add_slot(new_appt, 'new', unavailable=1)
	result.add_slot(appt, 'delete', unavailable=1)

	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def appointment_delete(request, appointment, start, all_slots,
						timeout_id, notify_client=True, username=None):
	result = AjaxResult(timeout_id)

	try:
		start_dt = convert_timestamp(start)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	if type(all_slots) != bool:
		result.error('All slots flag in invalid format.')
		return result.dump()

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	try:
		appointment_id = int(appointment)
		appt = Appointment.objects.get(healer=healer, id=appointment_id)

		schedule_permission_result = check_schedule_permission(healer,
			location=appt.location)
		if schedule_permission_result is not None:
			result.error(schedule_permission_result)
			return result.dump()

	except (Appointment.DoesNotExist, ValueError):
		result.error('Could not find appointment<br />%s<br />%s' % (healer.user.username, appointment))
		return result.dump()

	if all_slots or appt.is_single():
		appt.cancel(healer.user)
		result.add_slot(appt, 'delete', unavailable=1)
	else:
		updated_appt, appt = appt.cancel_single(start_dt)
		result.add_slot(updated_appt, 'delete' if updated_appt.canceled else 'update', unavailable=1)

	appt.notify_canceled(healer.user, is_wellness_center(request.user), notify_client)

	return result.dump()


@dajaxice_register
def facebook_login(request, access_token, signed_request):
	dajax = Dajax()
	access = OAuthAccess('facebook')

	if access_token and signed_request:
		data = access.parse_signed_request(signed_request)
		if data:
			auth_token = OAuth20Token(access_token)
			user, error = access.callback(request, access, auth_token, is_ajax=True)
			if user:
				client = user.client
				dajax.script('facebookLoginSuccess(%s);' % client.id)
			else:
				dajax.script("showResult('%s', 'Error')" % error)
		else:
			dajax.script("showResult('Can\\'t login with facebook.', 'Error')")

	return dajax.json()


@dajaxice_register
@user_authenticated_ajax
def seen_availability_help(request):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	healer.seen_availability_help = True
	healer.save()

	return json.dumps(True)


@dajaxice_register
@user_authenticated_ajax
def seen_appointments_help(request):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	healer.seen_appointments_help = True
	healer.save()

	return json.dumps(True)


@dajaxice_register
@user_authenticated_ajax
def timeoff_new(request, start, end, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	try:
		start_dt, end_dt = prepare_dates(start, end, check_past=False, check_diff_days=False)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer

	timeslot = Vacation(healer=healer)
	timeslot.set_dates(start_dt, end_dt)
	timeslot.save()

	result.add_slot(timeslot, 'new', unavailable=1)
	return result.dump()


def get_timeslot(request, username, result, timeslot_id):
	healer, error = get_healer_generic(request, username, result)
	if error:
		return healer
	try:
		timeslot_id = int(timeslot_id)
		timeslot = Vacation.objects.get(healer=healer, id=timeslot_id)
	except (Vacation.DoesNotExist, ValueError):
		result.error('Could not find timeslot<br />%s<br />%s' % (healer.user.username, timeslot_id))
		error = True
		timeslot = result.dump()
	return timeslot, error


@dajaxice_register
@user_authenticated_ajax
def timeoff_update(request, timeslot_id, start, end, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	try:
		start_dt, end_dt = prepare_dates(start, end, check_past=False, check_diff_days=False)
	except ValueError as e:
		result.error(str(e))
		return result.dump()

	timeslot, error = get_timeslot(request, username, result, timeslot_id)
	if error:
		return timeslot
	timeslot.set_dates(start_dt, end_dt)
	timeslot.save()

	result.add_slot(timeslot, 'update', unavailable=1)
	return result.dump()


@dajaxice_register
@user_authenticated_ajax
def timeoff_delete(request, timeslot_id, timeout_id, username=None):
	result = AjaxResult(timeout_id)

	timeslot, error = get_timeslot(request, username, result, timeslot_id)
	if error:
		return timeslot

	result.add_slot(timeslot, 'delete', unavailable=1)
	timeslot.delete()

	return result.dump()


@dajaxice_register
def load_wcenter_provider_treatments(request, wcenter_id, healer_id, location_id=None):
	def get_location():
		if location_id is not None:
			return Location.objects.get(pk=location_id)

	wellness_center = WellnessCenter.objects.get(pk=wcenter_id)
	healer = Healer.objects.get(pk=healer_id)
	location = get_location()
	treatment_types, treatment_lengths, treatment_length_bar, available_treatment_lengths = \
		get_tts_ttls_tbar_avail_ttls(request.user, wellness_center, healer, location)
	html = render_to_string('healers/treatment_types_bar.html', {
		'treatment_types': treatment_types,
		'locations_objects': get_locations(wellness_center, selected_location=location),
		'treatment_lengths': treatment_lengths,
		'treatment_length_bar': treatment_length_bar,
		'provider_mode': True,
		'healer_id': healer_id})
	return json.dumps({'html': html,
		'available_treatment_lengths': available_treatment_lengths})


@dajaxice_register
def load_wcenter_providers(request, wcenter_id, treatment_type_length_id):
	def get_healers_for_treatment_type():
		def get_treatment_type_length():
			def get_tlength():
				# get healer ttls for center
				wcenter_ttl = WellnessCenterTreatmentTypeLength.objects.filter(
					wellness_center=wcenter, healer=healer)
				if wcenter_ttl.exists():
					# get healer ttls
					healer_ttls = wcenter_ttl[0].treatment_type_lengths
					healer_tts_ids = healer_ttls.values_list('treatment_type', flat=True)
					# check if this treatment type/length is in the healer's selection
					if treatment_type.pk in healer_tts_ids:
						t_lengths = healer_ttls.filter(treatment_type=treatment_type,
							length=treatment_type_length.length)
						if t_lengths.exists():
							# return the correct treatment length for healer
							return t_lengths[0]
					else:
						return treatment_type_length
				else:
					return treatment_type_length

			t_length = get_tlength()
			if t_length is not None:
				treatment_type_lengths[t_length.pk] = t_length.json_object()
				return t_length

		healers_output = []
		for healer in healers:
			for wcenter_treatment_types in healer.wellness_center_treatment_types.filter(wellness_center__pk=wcenter_id):
				if treatment_type in wcenter_treatment_types.treatment_types.all():
					t_length = get_treatment_type_length()
					if t_length is not None:
						healers_output.append(
							{'healer': healer,
							'treatment_type_length': t_length})
						break
		return healers_output

	wcenter = WellnessCenter.objects.get(pk=wcenter_id)

	treatment_type_length = TreatmentTypeLength.objects.get(pk=treatment_type_length_id)
	treatment_type = treatment_type_length.treatment_type
	healers = get_available_healers(request.user, wcenter, treatment_type)

	treatment_type_lengths = {}

	healers = get_healers_for_treatment_type()

	html = render_to_string('healers/wcenter_providers_treatment_mode.html', {
		'healers': healers})

	return json.dumps({
		'html': html,
		'treatment_type_lengths': treatment_type_lengths})


def get_wcenter_location_ids_from_wcenter_id(wcenter_id):
	return get_wcenter_location_ids(WellnessCenter.objects.get(pk=wcenter_id).user)


@dajaxice_register
def load_wcenter_schedule_data(request, healer_id, wcenter_id, treatment_type_id):
	def format_date(date):
		return date.strftime('%H:%S')

	def get_other_healers_appointments_json():
		resultList = Timeslot.prepare_json_slots(timeslot_keys, get_other_healers_appointments(healer, locations))
		return json.dumps(resultList)

	def get_wcenter_rooms():
		rooms = get_rooms(TreatmentType.objects.get(pk=treatment_type_id), locations)
		return list(rooms.values_list('pk', flat=True))

	healer = Healer.objects.get(pk=healer_id)
	locations = get_wcenter_location_ids_from_wcenter_id(wcenter_id)

	if request.user.is_anonymous():
		client = None
	else:
		try:
			client = Client.objects.get(user=request.user)
		except ObjectDoesNotExist:
			client = None

	data = {
	'username': healer.user.username,
	'name': healer.user.get_full_name(),
	'bookAheadDays': healer.bookAheadDays,
	'first_bookable_time': healer.get_first_bookable_time(),
	'setup_time': healer.setup_time,
	'timeslot_list': getTimeslotsReadonly(request=request,
		treatment_type_id=treatment_type_id, healer=healer,
		wcenter_id=wcenter_id),
	'other_healers_appointments': get_other_healers_appointments_json(),
	'office_hours_start': format_date(healer.office_hours_start),
	'office_hours_end': format_date(healer.office_hours_end),
	'appt_schedule_or_request': healer.appt_schedule_or_request(client),
	'rooms': get_wcenter_rooms(),
	}
	return json.dumps(data)


# @dajaxice_register
# def treatment_types_bar(request, healer):
#   try:
#	   healer = Healer.objects.get(user__username__iexact=healer)
#   except (Healer.DoesNotExist, ValueError):
#	   return json.dumps('Could not find that healer')

#   treatment_types = TreatmentType.objects.filter(healer=healer, is_deleted=False).order_by('is_default').reverse()
#   treatment_lengths = TreatmentTypeLength.objects.select_related().filter(treatment_type__in=treatment_types, is_deleted=False)

#   treatment_length_bar = treatment_lengths.count()>treatment_types.count()
#   if not treatment_length_bar:
#	   for tl in treatment_lengths:
#		   tl.description = tl.treatment_type.description

#   ctx = {
#	   'treatment_types': treatment_types,
#	   'treatment_lengths': treatment_lengths,
#	   'treatment_length_bar': treatment_length_bar
#   }

#   treatment_types_bar = render_to_string('healers/treatment_types_bar.html', ctx)
#   dajax = Dajax()
#   dajax.script("$('#treatment_types_bar').html('%s')" % escapejs(treatment_types_bar))
#   dajax.script("$('.highlight_container span, .highlight_button').click(clickContained)")
#   dajax.script("$('.highlight_container span').click(highlightButton)")

#   if len(treatment_types) == 1:
#	   treatment_json = treatment_types[0].json_object()
#	   dajax.script("var treatment_type = %s; changeTreatmentType(treatment_type, true)" % treatment_json)
#	   if len(treatment_lengths) == 1:
#		   dajax.script("var treatment_type = %s; changeTreatment(treatment_type.lengths[0])" % treatment_json)

#   return dajax.json()

#@user_authenticated_ajax
#def new_treatment_length(request, data):
#   dajax = Dajax()
#   qd = QueryDict(data)
#   form = TreatmentTypeLengthForm(qd)
#
#   try:
#	   treatment_type_id = qd['treatment_type_id']
#	   treatment = TreatmentType.objects.get(id=treatment_type_id, healer=request.user.client.healer)
#   except (TreatmentType.DoesNotExist, KeyError):
#	   dajax.script('newTreatmentLengthFailure(%s);' % "Could not find that Treatment Type")
#	   return dajax.json()
#
#   if form.is_valid():
#	   treatment_length = form.save(commit=False)
#	   treatment_length.treatment_type = treatment
#	   treatment_length.save()
#
#	   dajax.script("newTreatmentLengthSuccess();")
#
#   else:
#	   dajax.remove_css_class('#add_length_dialog_form input','error')
#	   error_list = ""
#	   for error in form.errors:
#		   dajax.add_css_class('#add_length_dialog_form #id_%s' % error,'error')
#		   error_list += ("<li>%s</li>" % error)
#
#	   dajax.assign('#add_length_dialog_error_list','innerHTML', error_list)
#	   dajax.add_css_class('#add_length_dialog_errors','ui-helper-clearfix')
#	   dajax.script('newTreatmentLengthFailure();')
#
#   return dajax.json()
