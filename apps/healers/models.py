# -*- coding: utf-8 -*-

import json
import urllib
import urllib2
from copy import deepcopy
from calendar import timegm
from datetime import datetime, timedelta, time, date
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc
from itertools import groupby

from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.query_utils import Q
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import pluralize, slugify

from pinax.apps.account.models import EmailAddress
from friends.models import Friendship, FriendshipManager, FriendshipInvitation, FriendshipInvitationManager

from sync_hs.models import CalendarSyncQueueTask, ACTION_DELETE, ACTION_UPDATE, ACTION_NEW, API_CHOICES, UnavailableCalendar
from modality.models import ModalityCategory, Modality
from intake_forms.models import Answer, IntakeFormSentHistory
from util import full_url, absolute_url
from clients.models import Client, ClientLocation
from payments.models import Payment

from healers.fields import SeparatedValuesField
from healers.sms import send_sms
import healers

LOCATION_COLOR_LIST = [
	'#68A1E5',
	'#5FBF87',
	'#928ECF',
	'#F2A640',
	'#A7A77D',
	'#BE9494',
	'#E0C240',
	'#D96666',
	'#59BFB3',
	'#C09B64',
	'#BFBF4D',
	'#DF80F7',
	'#8BE2B8',
	'#E69229',
	'#9EDF4B',
   '#5C7BBE',
   '#7EECEC',
	'#52E08B',
   '#8BB83B',
	'#ECE766',
]

#TODO: remove
def is_conflict(slots, start, end):
	conflicts = get_conflicts(slots, start, end)
	return len(conflicts) > 0

#TODO: remove
def get_conflicts(slots, start, end):
	result_slots = []
	for s in slots:
		if ((s.start <= start < s.end) or (s.start < end <= s.end)
				or (start <= s.start < end) or (start < s.end <= end)):
			result_slots.append(s)

	return result_slots

def fix_weekday(day):
	return ((day+1) % 7) + 1

def date_range_text(start, end):
	return "%s at %s %s - %s %s" % (start.strftime("%A, %B %d"),
								  start.strftime("%I:%M").lstrip('0'), start.strftime("%p").lower(),
								  end.strftime("%I:%M").lstrip('0'), end.strftime("%p").lower())

def get_date_minutes(date_dt):
	return date_dt.date(), get_minutes(date_dt)

def get_minutes(date_dt):
	return date_dt.hour*60 + date_dt.minute

def get_timestamp(date_obj):
	return timegm(date_obj.timetuple())

def total_seconds(td):
	""" Total seconds in time delta """
	return td.seconds + td.days * 24 * 3600

def format_dates(dates):
	""" Format dates in list """
	return ["%d/%02d" % (d.month, d.day) for d in dates]

def combine_date_minutes(date_obj, minutes):
	""" Combine date and minutes in datetime object """
	return datetime.combine(date_obj, time()) + timedelta(minutes=minutes)


class Timezone():
	TIMEZONE_CHOICES = (
		('-05:00', '-5:00: Eastern Time (US & Canada)'),
		('-06:00', '-6:00: Central Time (US & Canada)'),
		('-07:00', '-7:00: Mountain Time (US & Canada)'),
		('-08:00', '-8:00: Pacific Time (US & Canada)'),
		('-09:00', '-9:00: Alaska'),
		('-10:00', '-10:00: Hawaii'),
		('-11:00', '-11:00: Midway Island, Samoa'),
		('-12:00', '-12:00: Eniwetok, Kwajalein'),
		('+12:00', '+12:00: Auckland, Wellington, Fiji'),
		('+11:00', '+11:00: Magadan, Solomon Isl'),
		('+10:00', '+10:00: Eastern Australia, Guam'),
		('+09:30', '+9:30: Adelaide, Darwin'),
		('+09:00', '+9:00: Tokyo, Seoul, Osaka'),
		('+08:00', '+8:00: Beijing, Perth, Singapore, HK'),
		('+07:00', '+7:00: Bangkok, Hanoi, Jakarta'),
		('+06:30', '+6:30: Rangoon, Cocos'),
		('+06:00', '+6:00: Almaty, Dhaka, Colombo'),
		('+05:45', '+5:45: Kathmandu'),
		('+05:30', '+5:30: Bombay, Calcutta, Delhi'),
		('+05:00', '+5:00: Ekaterinburg, Karachi'),
		('+04:30', '+4:30: Kabul'),
		('+04:00', '+4:00: Abu Dhabi, Muscat, Baku'),
		('+03:30', '+3:30: Tehran'),
		('+03:00', '+3:00: Riyadh, Moscow, St Peter'),
		('+02:00', '+2:00: Kaliningrad, South Africa'),
		('+01:00', '+1:00: Copenhagen, Madrid, Paris'),
		('+00:00', 'GMT: W. Europe, London, Lisbon'),
		('-01:00', '-1:00: Azores, Cape Verde Islands'),
		('-02:00', '-2:00: Mid-Atlantic'),
		('-03:00', '-3:00: Brazil, Buenos Aires'),
		('-03:30', '-3:30: Newfoundland'),
		('-04:00', '-4:00: Atlantic Time (Canada)'),
		('-04:30', '-4:30: Caracas'),
	)

	TIMEZONE_CODES = {
		'-12:00': 'Pacific/Kwajalein',
		'-11:00': 'Pacific/Midway',
		'-10:00': 'Pacific/Honolulu',
		'-09:00': 'America/Anchorage',
		'-08:00': 'America/Los_Angeles',
		'-07:00': 'America/Denver',
		'-06:00': 'America/Chicago',
		'-05:00': 'America/New_York',
		'-04:30': 'America/Caracas',
		'-04:00': 'America/Halifax',
		'-03:30': 'America/St_Johns',
		'-03:00': 'America/Argentina/Buenos_Aires',
		'-02:00': 'Atlantic/South_Georgia',
		'-01:00': 'Atlantic/Azores',
		'+00:00': 'Europe/London',
		'+01:00': 'Europe/Paris',
		'+02:00': 'Europe/Tallinn',
		'+03:00': 'Asia/Baghdad',
		'+03:30': 'Asia/Tehran',
		'+04:00': 'Asia/Tbilisi',
		'+04:30': 'Asia/Kabul',
		'+05:00': 'Asia/Tashkent',
		'+05:30': 'Asia/Calcutta',
		'+05:45': 'Asia/Katmandu',
		'+06:00': 'Asia/Bishkek',
		'+06:30': 'Asia/Rangoon',
		'+07:00': 'Asia/Bangkok',
		'+08:00': 'Asia/Ulaanbaatar',
		'+09:00': 'Asia/Tokyo',
		'+09:30': 'Australia/Darwin',
		'+10:00': 'Australia/Sydney',
		'+11:00': 'Pacific/Guadalcanal',
		'+12:00': 'Pacific/Auckland'
	}


class HealerCompleteManager(gis_models.GeoManager):
	def get_queryset(self):
		return super(HealerCompleteManager, self).get_queryset() \
			.filter(user__avatar__isnull=False) \
			.exclude(user__is_active=False) \
			.exclude(profileVisibility=Healer.VISIBLE_CLIENTS) \
			.exclude(about='') \
			.distinct()

	def within_50_miles(self, zipcode):
		return self.get_queryset().filter(
			clientlocation__location__point__distance_lte=(
				zipcode.point, D(mi=50)))


class Healer(Client):

	DEFAULT_TIMESLOT_LENGTH_CHOICES = (
		(1.0, '0:30'),
		(2.0, '1:00'),
		(3.0, '1:30'),
		(3.5, '2:00'),
		(4.0, '2:30'),
		(4.5, '3:00'),
		(5.0, '3:30'),
		(5.5, '4:00'),
		(6.0, '4:30'),
		(6.5, '5:00'),
	)

	CONFIRM_MANUAL = 1
	CONFIRM_MANUAL_NEW = 2
	CONFIRM_AUTO = 3
	CONFIRMATION_CHOICES = (
		(CONFIRM_MANUAL, 'Manually confirm all appointments'),
		(CONFIRM_MANUAL_NEW, 'Manually confirm appointments for new clients only'),
		(CONFIRM_AUTO, 'Automatically confirm all appointments'),
	)

	INTAKE_FORM_PROMPT = 1
	INTAKE_FORM_EMAIL = 2
	INTAKE_FORM_NONE = 3
	INTAKE_FORM_BOOKING_CHOICES = (
		(INTAKE_FORM_PROMPT, 'Prompt my clients to fill out my Intake Form online after booking'),
		(INTAKE_FORM_EMAIL, 'Send my clients an email with a link to my Intake Form after booking'),
		(INTAKE_FORM_NONE, 'No Intake Form on booking'),
	)

	VISIBLE_EVERYONE = 0
#	VISIBLE_REGISTERED = 1
	VISIBLE_CLIENTS = 2
	VISIBLE_DISABLED = 3

	SCHEDULE_VISIBILITY_CHOICES = (
		(VISIBLE_EVERYONE, 'Visible to Everyone'),
#		(VISIBLE_REGISTERED, 'Visible to Registered HealerSource Users Only'),
		(VISIBLE_CLIENTS, 'Visible to My Clients Only'),
		(VISIBLE_DISABLED, 'Only Me (Preview)')
	)

	REVIEW_PERMISSION_CHOICES = (
		(VISIBLE_EVERYONE, 'Everyone'),
		(VISIBLE_CLIENTS, 'My Clients Only'),
		(VISIBLE_DISABLED, 'Nobody (Hide All Current Reviews)')
	)

	PROFILE_VISIBILITY_CHOICES = (
		(VISIBLE_EVERYONE, 'Visible to Everyone'),
#		(VISIBLE_REGISTERED, 'Visible to Registered HealerSource Users Only'),
		(VISIBLE_CLIENTS, 'Visible to My Clients Only'),
	)

	SCREEN_ALL = 0
	SCREEN_NOT_CONTACTS = 1
	SCREEN_NONE = 2

	CLIENT_SCREENING_CHOICES = (
		(SCREEN_ALL, 'Manually Screen All New Clients'),
		(SCREEN_NOT_CONTACTS, 'Auto Approve New Clients who Ive Imported from Facebook/Google'),
		(SCREEN_NONE, 'Automatically Approve All New Clients'),
	)

	BOOKING_REQUIRED_FULL_AMOUNT = 1
	BOOKING_REQUIRED_CARD = 2
	BOOKING_NOTHING_REQUIRED = 3

	BOOKING_PAYMENT_REQUIREMENT_CHOICES = (
		(BOOKING_REQUIRED_FULL_AMOUNT, 'Require full amount on booking'),
		(BOOKING_REQUIRED_CARD, "Require client to enter credit card, but don't charge anything"),
		(BOOKING_NOTHING_REQUIRED, 'Clients can book without credit card'),
	)

	BOOKING_HEALERSOURCE_FEE_PERCENTAGE = 1
	BOOKING_HEALERSOURCE_FEE_FIXED = 2

	BOOKING_HEALERSOURCE_FEE_CHOICES = (
		(BOOKING_HEALERSOURCE_FEE_FIXED, '$%d / month flat rate' % settings.BOOKING_HEALERSOURCE_FEE),
		(BOOKING_HEALERSOURCE_FEE_PERCENTAGE, '1% of All Transactions'),
	)

	PROFILE_REMINDER_INTERVAL_CHOICES = ((1, '1 week'),
										(2, '2 weeks'),
										(4, '1 month'),
										(8, '2 months'))

	GOOGLE_CALENDAR_TITLE = "Healersource Appointments"
	SCHEDULE_PERMISSION = 'healers.can_use_wcenter_schedule'
	NOTES_PERMISSION = 'healers.can_use_notes'
	BOOKING_PERMISSION = 'healers.can_use_booking_no_fee'

	GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_DAYS = 1
	GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_MONTHS = 2
	GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_YEARS = 3

	GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_LABELS = {
		GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_DAYS: 'days',
		GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_MONTHS: 'months',
		GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_YEARS: 'years'}

	GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_CHOICES = GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_LABELS.items()

	defaultTimeslotLength = models.FloatField(default = 3.0, choices = DEFAULT_TIMESLOT_LENGTH_CHOICES)
	bookAheadDays = models.IntegerField(default = 90)
	leadTime = models.PositiveIntegerField(default = 24)
	manualAppointmentConfirmation = models.PositiveSmallIntegerField(default = CONFIRM_MANUAL, choices = CONFIRMATION_CHOICES)
	intakeFormBooking = models.PositiveSmallIntegerField(default=INTAKE_FORM_PROMPT, choices=INTAKE_FORM_BOOKING_CHOICES)
	scheduleVisibility = models.PositiveSmallIntegerField(default = VISIBLE_DISABLED, choices = SCHEDULE_VISIBILITY_CHOICES)
	profileVisibility = models.PositiveSmallIntegerField(default = VISIBLE_EVERYONE, choices = PROFILE_VISIBILITY_CHOICES)
	phonesVisibility = models.PositiveSmallIntegerField(default = VISIBLE_EVERYONE, choices = PROFILE_VISIBILITY_CHOICES)
	client_screening = models.PositiveSmallIntegerField(default = SCREEN_ALL, choices = CLIENT_SCREENING_CHOICES)
	setup_time = models.PositiveSmallIntegerField('Setup time between clients', default=30)
	smart_scheduler_avoid_gaps_num = models.PositiveSmallIntegerField('Number of slots available if first one of the day is booked', default=0)
	profile_completeness_reminder_interval = models.PositiveSmallIntegerField(default = 4, choices = PROFILE_REMINDER_INTERVAL_CHOICES)
	profile_completeness_reminder_lastdate = models.DateField(blank=True, null=True)

	timezone = models.CharField("Timezone", max_length="6", choices=Timezone.TIMEZONE_CHOICES, default=Timezone.TIMEZONE_CHOICES[0][0])

	scheduleUpdatedThrough = models.DateField(default="1969-08-17")

	google_calendar_id = models.CharField(max_length=1024, blank=True)
	google_calendar_sync_retries = models.PositiveIntegerField(default=0)
	google_email = models.EmailField(blank=True)

	seen_availability_help = models.BooleanField(default=False)
	seen_appointments_help = models.BooleanField(default=False)

	office_hours_start = models.TimeField(default="10:00:00")
	office_hours_end = models.TimeField(default="20:00:00")

	years_in_practice = models.CharField(max_length=4, blank=True, default="")
	send_notification = models.BooleanField(default=True)
	cancellation_policy = models.TextField(_("cancellation_policy"), blank=True, default="")
	additional_text_for_email = models.TextField(_("additional info"), blank=True, default="")

	# This is a temporary HACK for Ariel so she can have 2 providers at 1 Location. Instead of building new functionality,
	# we can just set the label on the public pages to something other than "Location: "
	location_bar_title = models.CharField(max_length=36, blank=True, default='Locations: ')

	setup_step = models.PositiveSmallIntegerField(default=0)

	wellness_center_permissions = models.ManyToManyField('WellnessCenter', blank=True, null=True)

	ratings_1_star = models.PositiveIntegerField(default=0)
	ratings_2_star = models.PositiveIntegerField(default=0)
	ratings_3_star = models.PositiveIntegerField(default=0)
	ratings_4_star = models.PositiveIntegerField(default=0)
	ratings_5_star = models.PositiveIntegerField(default=0)
	ratings_average = models.FloatField(default=0)

	review_permission = models.PositiveSmallIntegerField(
		default=VISIBLE_EVERYONE, choices=REVIEW_PERMISSION_CHOICES)

	send_sms_appt_request = models.BooleanField(default=True)
	schedule_full_width = models.BooleanField(default=False)
	schedule_start_from_sunday_setting = models.BooleanField(default=False)
	booking_optional_message_allowed = models.BooleanField(default=True)
	remote_sessions = models.BooleanField(default=False)
	gift_certificates_enabled = models.BooleanField(default=False)
	gift_certificates_expiration_period = models.PositiveIntegerField(default=1)
	gift_certificates_expiration_period_type = models.PositiveSmallIntegerField(
		default=GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_YEARS,
		choices=GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_CHOICES)

	#denormalisation
	#date_joined = models.DateTimeField(_('date joined'), default=dj_timezone.now)
	default_modality = models.CharField(max_length=64, default=settings.DEFAULT_MODALITY_TEXT)
	default_location = models.CharField(max_length=64, default=settings.DEFAULT_LOCATION_TEXT)

	deposit_percentage = models.PositiveIntegerField(default=100)
	booking_payment_requirement = models.PositiveSmallIntegerField(default=BOOKING_REQUIRED_FULL_AMOUNT,
		choices=BOOKING_PAYMENT_REQUIREMENT_CHOICES)
	booking_healersource_fee = models.PositiveSmallIntegerField(default=BOOKING_HEALERSOURCE_FEE_PERCENTAGE,
		choices=BOOKING_HEALERSOURCE_FEE_CHOICES)

#	accept_outcalls = models.BooleanField(default=False)
	objects = gis_models.GeoManager()
	complete = HealerCompleteManager()

	class Meta:
		verbose_name = _("healers")
		verbose_name_plural = _("healers")
		permissions = (
			('can_use_wcenter_schedule', 'Can use wellness center schedule'),
			('can_use_notes', 'Can use notes'),
			('can_use_booking_no_fee', 'Can use booking without fees'),
		)

	# def __unicode__(self):
	# 	return self.user.username

	def json_object(self):
		healer = {
			'id': self.id,
			'username': self.user.username,
			'fullname': super(Healer, self).__unicode__(),
			'bookAheadDays': self.bookAheadDays,
			'setupTime': self.setup_time,
			'officeHoursStart': self.office_hours_start.strftime('%H:%M'),
			'officeHoursEnd': self.office_hours_end.strftime('%H:%M')
		}
		return json.dumps(healer)

	def clients(self):
		return [o["friend"] for o in Clients.objects.friends_for_user(self.user)]

	def full_name(self):
		return super(Healer, self).__unicode__()

	def get_full_url(self, view='healer_public_profile', absolute=True):
		if view == 'healer_public_profile':
			if self.default_modality == '' or self.default_location == '':
				return super(Healer, self).get_full_url(
					'healer_my_profile', absolute)
		return super(Healer, self).get_full_url(
			view, absolute)

	#this method should be used, insted of upper one
	def healer_profile_url(self, absolute=True):
		return self.get_full_url(absolute=absolute)

	def healer_short_profile_url(self):
		return self.get_full_url(view='healer_my_profile')

	def is_fill_warning(self):
		if self.about == "" or not self.user.avatar_set.count():
			return True
		return False

	def is_confirmed_email(self):
		return EmailAddress.objects.filter(user=self.user,
			verified=True).exists()

	def update_rating(self, rating, prev_rating=None):
		if prev_rating:
			field_name = 'ratings_%d_star' % prev_rating
			if hasattr(self, field_name):
				value = getattr(self, field_name) - 1
				if value >= 0:
					setattr(self, field_name, value)
		field_name = 'ratings_%d_star' % rating
		if hasattr(self, field_name):
			setattr(self, field_name, getattr(self, field_name) + 1)
			self.ratings_average = float(1*self.ratings_1_star + 2*self.ratings_2_star + 3*self.ratings_3_star + 4*self.ratings_4_star + 5*self.ratings_5_star)
			self.ratings_average = self.ratings_average/self.ratings_sum()
			self.save()

	def ratings_sum(self):
		return self.ratings_1_star + self.ratings_2_star + self.ratings_3_star + self.ratings_4_star + self.ratings_5_star

	def ratings_perc(self, rating):
		ratings_sum = self.ratings_sum()
		return float(rating)*100/ratings_sum if ratings_sum else 0

	def ratings_1_star_perc(self):
		return self.ratings_perc(self.ratings_1_star)

	def ratings_2_star_perc(self):
		return self.ratings_perc(self.ratings_2_star)

	def ratings_3_star_perc(self):
		return self.ratings_perc(self.ratings_3_star)

	def ratings_4_star_perc(self):
		return self.ratings_perc(self.ratings_4_star)

	def ratings_5_star_perc(self):
		return self.ratings_perc(self.ratings_5_star)

	def is_schedule_visible(self, user, is_client=None):
		""" Check schedule visibility for user """
#		if self.healer_treatment_types.count() == 0:
#			return False

		if self.user == user:
			return True

		if self.scheduleVisibility == Healer.VISIBLE_DISABLED:
			return False

#		elif self.scheduleVisibility == Healer.VISIBLE_REGISTERED:
#			if not user.is_authenticated():
#				visible = False

		elif self.scheduleVisibility == Healer.VISIBLE_CLIENTS:
			if not user.is_authenticated():
				return False
			else:
				return is_client if (is_client is not None) else is_my_client(self.user, user)

		return True

	def is_visible_to(self, user, is_client=None):
		visible = True
#		if self.profileVisibility == Healer.VISIBLE_REGISTERED:
#			visible = user.is_authenticated()

		if self.profileVisibility == Healer.VISIBLE_CLIENTS:
			if not user.is_authenticated():
				visible = False
			else:
				visible = is_client if (is_client is not None) else is_my_client(self.user, user)

		return visible

	def get_modalities_categories(self):
		return ModalityCategory.objects.filter(modality__healer=self).distinct('title')

	def is_review_permission(self, user, is_client=None):
		""" Check review permission for user """
		if self.user == user:
			return True

		if self.review_permission == Healer.VISIBLE_DISABLED:
			return False
		elif self.review_permission == Healer.VISIBLE_CLIENTS:
			if not user.is_authenticated():
				return False
			else:
				return is_client if (is_client is not None) else is_my_client(self.user, user)

		return True

	def get_locations(self, user=None, is_client=None, show_deleted=False,
			skip_center_locations=False, wellness_center=False):
		def is_address_visible(location, user, is_my_client):
			location = location.location

			if ((user is None) or (is_my_client is None) or
					(location.addressVisibility == Healer.VISIBLE_EVERYONE)):
				return True

			elif location.addressVisibility == Healer.VISIBLE_DISABLED:
				return False

#			elif location.addressVisibility == Healer.VISIBLE_REGISTERED:
#				if not user.is_authenticated():
#					return False

			elif location.addressVisibility == Healer.VISIBLE_CLIENTS:
				if not user.is_authenticated() or not is_client:
					return False

			return True

		def get_json(location, wcenter_id, i=0, user=None, is_my_client=None):
			is_wellness_center = wcenter_id != 0

			loc = location.location
			address_text = loc.address_text()
			return {
				"text": str(loc).strip(),
				"address_text": address_text,
				"gmaps_address_text": loc.gmaps_link(address_text),
				"full_address_text": loc.full_address_text(address_text),
				"color": loc.color if loc.color else Location.get_next_color(i, is_wellness_center),
				"id": loc.id,
				"is_address_visible": is_address_visible(location, user, is_my_client),
				"city": loc.city,
				"state_province": loc.state_province,
				"book_online": int(loc.book_online),
				"is_deleted": loc.is_deleted,
				'wcenter_id': wcenter_id,
			}

		locations = []
		if not wellness_center:
			location_list = ClientLocation.objects.filter(client=self).order_by('-location__is_default')

			if not show_deleted:
				location_list = location_list.filter(location__is_deleted=False)

			if is_wellness_center(self):
				wcenter_id = self.id
			else:
				wcenter_id = 0

			for i in range(0, len(location_list)):
				locations.append(get_json(location_list[i], wcenter_id, i, user,
					is_client))

		if not skip_center_locations:
			i = 0
			if wellness_center:
				wcenters = [wellness_center]
			else:
				wcenters = self.get_wellness_centers()
			if self.user.has_perm(Healer.SCHEDULE_PERMISSION):
				for wcenter in wcenters:
					try:
						wcenter_locations = ClientLocation.objects.filter(
							client=wcenter, location__is_deleted=False)
						for location in wcenter_locations:
							locations.append(get_json(location, wcenter.id, i, user,
								is_client))
						i += 1
					except IndexError:
						pass

		return locations

	def get_wellness_centers(self):
		return WellnessCenter.objects.filter(user__in=[r.from_user for r in Referrals.objects.filter(to_user=self.user)])

	def get_locations_objects(self, only_visible=False):
		c_location_list = ClientLocation.objects.filter(client=self, location__is_deleted=False).order_by('-location__is_default')
		locations = []
		for client_location in c_location_list:
			location = client_location.location
			if only_visible:
				if location.book_online == location.BOOK_ONLINE_HIDDEN:
					continue
			locations.append(location)
		return locations

	def get_wellness_center_locations(self, location_id=None):
		locations = ClientLocation.objects.filter(client__in=self.get_wellness_centers()).order_by('-location__is_default')
		if location_id:
			locations = locations.filter(location__id=location_id)
		return locations

	def get_center_locations_objects(self):
		return [c_location.location for c_location in self.get_wellness_center_locations()]

	def default_location_city(self):
		try:
			client_location = ClientLocation.objects.filter(
				client=self,
				location__is_deleted=False,
				location__is_default=True)

			location = client_location[0].location
			city_text = location.city_text().strip()
			if city_text:
				return city_text
			else:
				return location.title

		except IndexError:
			pass

		return ''

	def is_google_calendar_sync_enabled(self):
		if self.google_email:
			return True

	def get_last_bookable_date(self):
		return self.get_local_time().date() + timedelta(days=self.bookAheadDays+1)

	def healer_under_profile_photo(self, no_locations=False,
		no_years_in_practice=False, is_center=False):

		""" this is ugly but efficient - we only hit the db and render templates as needed """

		if not no_locations:
			locations = self.get_locations()
		else:
			locations = ''

		ctx = {
			"healer": self,
			"locations": locations,
			'no_years_in_practice': no_years_in_practice,
		}
		if is_center:
			ctx['is_center'] = True
			ctx['number_of_providers'] = len(WellnessCenter.objects.get(pk=self.pk).get_healers_in_wcenter())
		else:
			ctx["referrals_to_me_count"] = Referrals.objects.referrals_to(self.user, count=True)

		return render_to_string("healers/healer_under_profile_photo.html", ctx)

	def healer_under_profile_photo_no_locations(self):
		return self.healer_under_profile_photo(True)

	def healer_under_profile_photo_no_years_in_practice(self):
		return self.healer_under_profile_photo(True, True)

	def center_item_under_profile_photo_on_homepage(self):
		return self.healer_under_profile_photo(True, True, True)

	def healer_specialties_html(self):
		""" this is ugly but efficient - we only hit the db and render templates as needed """

		from modality.models import Modality
		modalities = Modality.objects_approved.filter(healer=self, visible=True)[:7]

		return render_to_string("healers/healer_specialties.html", { "modalities": modalities })

	def get_local_time(self):
		now = settings.GET_NOW()
		if self.timezone:
			try:
				tz = timezone(Timezone.TIMEZONE_CODES[self.timezone])
				now_utc = utc.localize(now) # add utc timezone
				now_tz = tz.normalize(now_utc.astimezone(tz)) # convert to healer timezone
				return now_tz.replace(tzinfo=None) # remove tz to compare with naive datetime
			except Exception:
				return now
		else:
			return now

	def get_local_day(self):
		return self.get_local_time().replace(hour=0, minute=0, second=0, microsecond=0)

	def get_first_bookable_time(self):
		first_bookable_time = self.get_local_time() + timedelta(hours=self.leadTime)
		return first_bookable_time.replace(microsecond=0).isoformat()

	def appt_schedule_or_request(self, client):
		if (client and (self.user == client.user)) or Appointment.check_for_auto_confirm(self, client):
			return "Schedule"
		else:
			return "Request"

	def has_pointed_location(self):
		for location in self.clientlocation_set.all():
			if location.location.point:
				return True
		return False

	def completed_forms(self):
		forms = self.intake_forms.all()
		if forms.count() == 0:
			return Answer.objects.none()
		form = forms[0]

		return Answer.objects.filter(form=form)

	def incomplete_forms(self):
		forms = self.intake_forms.all()
		if forms.count() == 0:
			return []
		form = forms[0]
		incomplete = []

		for instance in IntakeFormSentHistory.objects.filter(healer=self).distinct('client'):
			try:
				form.answer_set.get(client=instance.client)
			except Answer.DoesNotExist:
				incomplete.append(instance)
		return incomplete

	def has_intake_form(self):
		return self.intake_forms.exists()

	def send_intake_form(self, client, url=None):
		def get_url():
			if url is None:
				return absolute_url(
					reverse('intake_form_answer', args=[self.user.username]))
			return url

		context = {
			'client': client,
			'healer': self,
			'url': get_url()
		}

		healers.utils.send_hs_mail(
			subject=render_to_string('intake_forms/emails/send_intake_form_subject.html', context),
			template_name='intake_forms/emails/send_intake_form_body.txt',
			ctx=context,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[client.user.email],
			fail_silently=True
		)

		IntakeFormSentHistory.objects.create(client=client, healer=self)

	def get_current_appointment_client(self):
		"""Return client of appointment in progress or appointment starting
		in 15 minutes or None if no appointments found.
		"""
		def datetime_intersect(t1start, t1end, t2start, t2end):
			return (t1start <= t2start <= t1end) or (t2start <= t1start <= t2end)

		start = datetime.now()
		end = start + timedelta(minutes=15)
		appts = self.healer_appointments.filter(confirmed=True).filter(Q(end_date__gte=start) | Q(end_date__isnull=True))
		appts = Appointment.generate_recurrency(appts, start, start + timedelta(days=1), skip_date_filter=True)
		appts = [apt for apt in appts if datetime_intersect(start, end, apt.start, apt.end)]
		if appts:
			return appts[0].client

	def get_step_name(self):
		try:
			return healers.utils.Setup_Step_Names.get_steps(self)[self.setup_step]
		except IndexError:
			return self.setup_step

	def get_all_treatment_types(self, include_deleted=False, only_center=False):
		treatment_types = set()
		wcenter_treatment_types = self.wellness_center_treatment_types.all()
		for wcenter_treatment_type in wcenter_treatment_types:
			wcenter_tts = wcenter_treatment_type.treatment_types
			if not include_deleted:
				wcenter_tts = wcenter_tts.filter(is_deleted=False)
			treatment_types |= set(wcenter_tts)
		if only_center:
			return treatment_types

		healer_treatment_types = self.healer_treatment_types
		if not include_deleted:
			healer_treatment_types = healer_treatment_types.filter(is_deleted=False)

		for healer_treatment_type in healer_treatment_types:
			treatment_types.add(healer_treatment_type)
		return list(treatment_types)

	def get_all_treatment_type_lengths(self):
		lengths = []
		for tt in self.get_all_treatment_types():
			lengths += list(TreatmentTypeLength.objects.filter(treatment_type=tt))
		return lengths

	def has_center_treatments(self, wcenter_user):
		wcenter = WellnessCenter.objects.get(user=wcenter_user)
		wcenter_tts = self.wellness_center_treatment_types.filter(wellness_center=wcenter)
		has_center_treatments = False
		if wcenter_tts:
			has_center_treatments = wcenter_tts[0].treatment_types.exists()
		if not has_center_treatments:
			wcenter_ttls = self.wellness_center_treatment_type_lengths.filter(wellness_center=wcenter)
			if wcenter_ttls:
				has_center_treatments = wcenter_ttls[0].treatment_type_lengths.exists()
		return has_center_treatments

	def is_enabled_gift_certificates(self):
		return self.has_enabled_stripe_connect() and self.gift_certificates_enabled

	def is_redeem_code_input_available(self):
		return not (not self.discount_codes.exists() and not self.is_enabled_gift_certificates())

	def is_payment_or_card_required(self):
		return (self.has_enabled_stripe_connect() and (self.is_card_required() or
			self.healer.booking_payment_requirement == self.BOOKING_REQUIRED_FULL_AMOUNT))

	def is_card_required(self):
		return self.healer.booking_payment_requirement == self.BOOKING_REQUIRED_CARD

	def services(self):
		tts = self.healer_treatment_types.filter(is_deleted=False)
		services = ''
		for tt in tts:
			services += tt.title + ': '
			lengths = tt.lengths.filter(is_deleted=False)
			lengths = [unicode(length) for length in lengths]
			services += ' | '.join(lengths)
			services += '<br>'

		if not services:
			modalities = [modality.title for modality in Modality.objects.filter(healer=self)]
			services += ', '.join(modalities)
		return services

	def is_completed_setup(self):
		return self.setup_step == len(healers.utils.Setup_Step_Names.get_steps(self))

	def has_specialities(self):
		result = Modality.objects_approved.filter(healer=self.healer, visible=True).exists()
		if not result:
			wcenter = is_wellness_center(self)
			if wcenter:
				return Modality.objects.filter(healer__in=wcenter.get_healers_in_wcenter()).exists()
			return False
		return True


class Concierge(Healer):
	pass


class WellnessCenter(Healer):
	PAYMENT_SCHEDULE_DISABLED = 1
	PAYMENT_EACH_PROVIDER_PAYS = 2
	PAYMENT_CENTER_PAYS = 3
	PAYMENT_CHOICES = (
		(PAYMENT_SCHEDULE_DISABLED, 'Disable schedule'),
		(PAYMENT_EACH_PROVIDER_PAYS, 'Each Provider pays individually for their schedule'),
		(PAYMENT_CENTER_PAYS, 'Center pays for everyone'),
	)

	payment_schedule_setting = models.PositiveSmallIntegerField(default=PAYMENT_SCHEDULE_DISABLED,
		choices=PAYMENT_CHOICES)
	clients_visible_to_providers = models.BooleanField(default=False)
	schedule_side_by_side_setting = models.BooleanField(default=False)
	schedule_trial_started_date = models.DateField(blank=True, null=True)
	schedule_dropdown_provider_list = models.BooleanField(default=False)
	common_availability = models.BooleanField(default=False)

	def is_schedule_trial_active(self):
		return (self.schedule_trial_started_date is not None and
			(settings.GET_NOW().date() - self.schedule_trial_started_date) <=
				timedelta(days=settings.SCHEDULE_TRIAL_NUMBER_OF_DAYS)
			)

	def is_healer_in_wcenter(self, healer_user):
		return Referrals.objects.filter(to_user=healer_user,
										from_user=self.user).count() > 0

	def get_healers_in_wcenter(self):
		referral_users = [o['friend']
						for o in Referrals.objects.referrals_from(self.user)]
		return Healer.objects.filter(user__in=referral_users)

	def get_location_ids(self):
		return ClientLocation.objects.filter(client=self).values_list(
			'location__pk', flat=True)

	def is_skip_provider_step(self):
		return self.user.username in settings.NO_PROVIDER_STEP_USERS


class Zipcode(gis_models.Model):
	code = models.CharField(max_length=5, db_index=True)
	city = models.CharField(max_length=50, blank=True)
	state = models.CharField(max_length=2, blank=True)
	population = models.PositiveIntegerField(blank=True, default=0)
	point = gis_models.PointField(spatial_index=True)
	objects = gis_models.GeoManager()

	def __unicode__(self):
		return self.code


class Address(models.Model):
	address_line1 = models.CharField("Address Line 1", max_length=42, blank=True)
	address_line2 = models.CharField("Address Line 2", max_length=42, blank=True)
	postal_code = models.CharField("Zip Code", max_length=10, blank=True,
									db_index=True)
	city = models.CharField(max_length=42, blank=True)
	state_province = models.CharField("State", max_length=42, blank=True)
	country = models.CharField('Country', max_length=42, blank=True)
	point = gis_models.PointField(spatial_index=True, blank=True, null=True)

	objects = gis_models.GeoManager()

	def __unicode__(self):
		return "%s, %s %s" % (self.city, self.state_province, str(self.country))

	def address_string(self):
		address = []
		if self.address_line1:
			address.append(self.address_line1)
		if self.address_line2:
			address.append(self.address_line2)
		if self.city:
			address.append(self.city)
		if self.state_province:
			address.append(self.state_province)
		if self.postal_code:
			address.append(self.postal_code)
		if self.country:
			address.append(self.country)

		return ','.join(address)

	def google_maps_request(self, force=False):
		if not (self.postal_code or (self.city and self.state_province)) and not force:
			self.point = None

		else:
			params = {'address': self.address_string().encode('utf-8'), 'sensor': 'false'}
			fp = urllib2.urlopen('http://maps.googleapis.com/maps/api/geocode/json?' + urllib.urlencode(params))
			data = fp.read()
			try:
				data = json.loads(data)
				point_data = data['results'][0]['geometry']['location']
				self.point = Point(point_data['lng'], point_data['lat'])
			except Exception as e:
				pass

	class Meta:
		verbose_name_plural = "Addresses"
#		unique_together = ("address_line1", "address_line2", "postal_code",
#						   "city", "state_province", "country")


class Location(Address):
	ADDRESS_VISIBILITY_CHOICES = (
		(Healer.VISIBLE_EVERYONE, 'Visible to Everyone'),
#		(Healer.VISIBLE_REGISTERED, 'Visible to Registered HealerSource Users Only'),
		(Healer.VISIBLE_CLIENTS, 'Visible to My Clients Only'),
		(Healer.VISIBLE_DISABLED, "Dont Show Address (Only Location Name)")
	)

	BOOK_ONLINE_DISABLED = 0
	BOOK_ONLINE_ENABLED = 1
	BOOK_ONLINE_HIDDEN = 2

	BOOK_ONLINE_CHOICES = (
		(BOOK_ONLINE_ENABLED, 'Enable Online Bookings at this Location'),
		(BOOK_ONLINE_DISABLED, 'Show Availability but Disable Online Bookings at this Location (Call to Book)'),
		(BOOK_ONLINE_HIDDEN, 'Hide This Location from Public View (only you can see it)'),
	)

	title = models.CharField("Location Name", max_length=42)
	timezone = models.CharField("Timezone", max_length="6", choices=Timezone.TIMEZONE_CHOICES, blank=True, default='')
	addressVisibility = models.PositiveSmallIntegerField("Full Address Visibility", default=Healer.VISIBLE_EVERYONE, choices=ADDRESS_VISIBILITY_CHOICES)
	book_online = models.PositiveIntegerField(default=BOOK_ONLINE_ENABLED, choices=BOOK_ONLINE_CHOICES)
	is_default = models.BooleanField(default=False)
	color = models.CharField("Color", max_length=7, default='', choices=([(c, c) for c in LOCATION_COLOR_LIST]))
	is_deleted = models.BooleanField(default=False)

	objects = gis_models.GeoManager()

	def slug(self):
		return slugify(self.title)

	def __unicode__(self):
		if not self.title.strip():
			self.title = self.address_line1
			self.save()

		return self.title

	def address_text(self, separator="\n\t"):
		address = []

		address_line1 = []
		if self.address_line1:
			address_line1.append(self.address_line1)
		if address_line1:
			address.append(", ".join(address_line1))

		if self.address_line2:
			address.append(self.address_line2)

		city = []
		if self.city:
			city.append(self.city)
		if self.state_province:
			city.append(self.state_province)
		city = [", ".join(city)]
		if self.postal_code:
			city.append(self.postal_code)

		if city:
			address.append(" ".join(city))

		if self.country:
			address.append(self.country)

		return separator.join(address)

	def full_address_text(self, address_text=None):
		address = []
		if self.title:	address.append(self.title)

		if not address_text:
			address_text = self.address_text()

		address.append(address_text)

		return "\n\t".join(address)

	def city_text(self):
		"""
		Returns City, State or Postal code
		"""
		city_text = ''
		if self.city:
			city_text = self.city
			if self.state_province:
				city_text += ', ' + self.state_province
		elif self.postal_code:
			city_text = self.postal_code

		if city_text == '':
			locations = Location.objects.filter(
				clientlocation__client=self.clientlocation_set.all()[0].client)
			for location in locations:
				if location.postal_code != '':
					city_text = '%s, %s' % (location.city,
											location.state_province)

		return city_text

	def gmaps_link(self, text=None, target="_blank"):
		gmaps_address_text = ' '.join([self.address_line1, self.city, self.state_province, self.country, self.postal_code])

		if not text:
			text = self.address_text(' ')

		return '<a href="https://maps.google.com/maps?q=%s" target="%s">%s</a>' % (gmaps_address_text, target, text)

	@classmethod
	def get_name(cls, obj):
		if obj and obj.location:
			return str(obj.location)
		else:
			return 'Unspecified'

	@classmethod
	def get_next_color(cls, position, reversed):
		colors_num = len(LOCATION_COLOR_LIST)
		position = position % colors_num
		if reversed:
			position = colors_num - position - 1
		return LOCATION_COLOR_LIST[position]

	def delete(self, using=None, **kwargs):
		if kwargs.pop("force", False):
			super(Location, self).delete(using)
		else:
			self.is_deleted = True
			self.save()
			if self.is_default:
				self.set_new_default()
			self.is_default = False

	def set_new_default(self):
		client_location = self.clientlocation_set.all()[:1][0]
		location = Location.objects\
			.filter(clientlocation__client=client_location.client,
					is_deleted=False)\
			.exclude(id=self.id)[0]
		location.is_default = True
		location.save()

	@property
	def healer(self):
		return ClientLocation.objects.get(location=self.location).client.healer

	@property
	def number_of_unconfirmed_appointments(self):
		appts = Appointment.objects.get_active(self.healer, is_wellness_center(self.healer).get_healers_in_wcenter())
		return appts.filter(confirmed=False, location=self).count()


class Room(models.Model):
	name = models.CharField('name', max_length=128)
	location = models.ForeignKey(Location, related_name="rooms")

	class Meta:
		ordering = ['name']

	def __unicode__(self):
		return self.name

	def as_dict(self):
		return {
			'id': self.id,
			'name': self.name,
			'location': self.location_id
		}

	def save(self, *args, **kwargs):
		# make sure room name is not duplicated
		try:
			room_id = Room.objects.get(name=self.name, location=self.location).pk
			if room_id != self.pk:
				return
		except:
			pass
		super(Room, self).save(*args, **kwargs)

	@classmethod
	def get_name(cls, obj):
		if obj and obj.room:
			return str(obj.room)
		else:
			return 'Unspecified'


class TreatmentType(models.Model):
	healer = models.ForeignKey(Healer, related_name="healer_treatment_types")
	rooms = models.ManyToManyField(Room, blank=True, null=True, related_name='treatment_types')
	title = models.CharField(max_length=42)
	description = models.TextField(default='', blank=True)
	is_default = models.BooleanField(default=False)
	is_deleted = models.BooleanField(default=False)

	def __unicode__(self):
		return self.title

	def slug(self):
		return slugify(self.title)

	def json_object(self):
		treatment = {'id': self.id,
					'lengths': [l.as_dict() for l in self.lengths.filter(is_deleted=False)],
					'title': unicode(self),
					'is_deleted': 1 if self.is_deleted else 0}
		return json.dumps(treatment)

	def delete(self, using=None, **kwargs):
		if kwargs.pop("force", False):
			super(TreatmentType, self).delete(using)
		else:
			self.is_deleted = True
			self.save()
			if self.is_default:
				self.set_new_default()

	def set_new_default(self):
		treatment = TreatmentType.objects.filter(healer=self.healer, is_deleted=False).exclude(id=self.id)[0]
		treatment.is_default = True
		treatment.save()

	def set_default(self):
		self.is_default = True
		self.save()
		TreatmentType.objects.filter(healer=self.healer, is_deleted=False).exclude(id=self.id).update(is_default=False)

	def save(self, *args, **kwargs):
		if not TreatmentType.objects.filter(is_deleted=False).count():
			self.is_default = True
		super(TreatmentType, self).save(*args, **kwargs)

	def get_available_location_ids(self):
		""" Return location ids of available locations for treatment type and
		None if all locations are available."""
		if self.rooms.exists():
			return list(set(self.rooms.all().values_list('location', flat=True)))

	def is_available_at_location(self, location):
		available_locations = self.get_available_location_ids()
		return available_locations is None or location.pk in available_locations


class WellnessCenterTreatmentType(models.Model):
	healer = models.ForeignKey(Healer, related_name="wellness_center_treatment_types")
	wellness_center = models.ForeignKey(WellnessCenter)
	treatment_types = models.ManyToManyField(TreatmentType, blank=True, null=True)

	def __unicode__(self):
		return self.wellness_center.user.get_full_name()


class TreatmentTypeLength(models.Model):
	treatment_type = models.ForeignKey(TreatmentType, null=False, related_name="lengths")
	length = models.PositiveIntegerField()  # length in minutes
	cost = models.CharField(max_length=10)
	is_default = models.BooleanField(default=False)
	is_deleted = models.BooleanField(default=False)

	def length_title(self):
		return "%s %s" % (self.length_format(), self.length_label())

	def __unicode__(self):
		return "%s - %s" % (self.length_title(), self.cost_format())

	def title(self):
		return '%s %s' % (self.treatment_type.title, self.length_title())

	def as_dict(self):
		return {'id': self.id,
				'type': self.treatment_type_id,
				'length': self.length,
				'cost': self.cost,
				'title': unicode(self),
				'title_center': self.length_title(),
				'name': self.treatment_type.title,
				'full_title': self.full_title(),
				'is_default': 1 if self.is_default else 0,
				'is_deleted': 1 if self.is_deleted or self.treatment_type.is_deleted else 0}

	def json_object(self):
		return json.dumps(self.as_dict())

	def full_title(self):
		return '%s %s' % (self.treatment_type.title, unicode(self))

	def cost_format(self):
		cost = ''
		if self.is_valid_cost():
			cost += '$'
		cost += self.cost
		return cost

	def length_format(self):
		return '%d:%02d' % divmod(self.length, 60)

	def is_valid_cost(self):
		try:
			return float(self.cost)
		except ValueError:
			return False

	def length_label(self):
		if self.length < 60:
			return 'min'
		return 'hours'

	def delete(self, using=None, **kwargs):
		center_ttls = WellnessCenterTreatmentTypeLength.objects.filter(treatment_type_lengths=self)
		for center_ttl in center_ttls:
			center_ttl.treatment_type_lengths.remove(self)

		if kwargs.pop("force", False):
			super(TreatmentTypeLength, self).delete(using)
		else:
			self.is_deleted = True
			self.save()
			if self.is_default:
				self.set_new_default()

	def set_new_default(self):
		length = self.treatment_type.lengths.filter(is_deleted=False).exclude(id=self.id)[0]
		length.is_default = True
		length.save()

	def set_default(self):
		self.is_default = True
		self.save()
		self.treatment_type.lengths.filter(is_deleted=False).exclude(id=self.id).update(is_default=False)

	def save(self, *args, **kwargs):
		if not self.treatment_type.lengths.filter(is_deleted=False).count():
			self.is_default = True
		super(TreatmentTypeLength, self).save(*args, **kwargs)

	class Meta:
		ordering = ['length', 'cost']


class WellnessCenterTreatmentTypeLength(models.Model):
	healer = models.ForeignKey(Healer, related_name="wellness_center_treatment_type_lengths")
	wellness_center = models.ForeignKey(WellnessCenter)
	treatment_type_lengths = models.ManyToManyField(TreatmentTypeLength, blank=True, null=True)

	def __unicode__(self):
		return self.wellness_center.user.get_full_name()


class TimeslotQuerySet(models.query.QuerySet):
	def filter_by_date(self, start, end=None):
		qs = self.filter((Q(end_date__isnull=False) & Q(end_date__gte=start)) | Q(end_date__isnull=True))
		if end:
			qs = qs.filter(start_date__lte=end)

		return qs

	def filter_by_datetime(self, start, end=None):
		start_filter = Q(end_date__gt=start) | (Q(end_date=start) & Q(end_time__gte=get_minutes(start)))
		qs = self.filter((Q(end_date__isnull=False) & start_filter) | Q(end_date__isnull=True))
		if end:
			end_filter = Q(start_date__lt=end) | (Q(start_date=start) & Q(start_time__lte=get_minutes(end)))
			qs = qs.filter(end_filter)

		return qs

	def exclude_by_datetime(self, start):
		start_filter = Q(end_date__gt=start) | (Q(end_date=start) & Q(end_time__gte=get_minutes(start)))
		qs = self.exclude((Q(end_date__isnull=False) & start_filter) | Q(end_date__isnull=True))

		return qs

	def before_date(self, date=None):
		if not date:
			date = settings.GET_NOW().date()
		qs = self.filter(start_date__lte=date)

		return qs


class TimeslotManager(models.Manager):
	def get_queryset(self):
		return TimeslotQuerySet(self.model, using=self._db)


class Timeslot(models.Model):
	REPEAT_CHOICES = (
		(rrule.DAILY, 'day'),
		(rrule.WEEKLY, 'week'),
	)

	start_date = models.DateField()
	end_date = models.DateField(null=True)
	start_time = models.PositiveSmallIntegerField()  # minute in day 0 - 1440
	end_time = models.PositiveSmallIntegerField()
	repeat_period = models.PositiveSmallIntegerField(choices=REPEAT_CHOICES, null=True, default=None)
	repeat_every = models.PositiveIntegerField(default=1, null=True)
	exceptions = SeparatedValuesField(null=True)

	objects = TimeslotManager()

	@property
	def start(self):
		return combine_date_minutes(self.start_date, self.start_time)

	@property
	def end(self):
		return combine_date_minutes(self.start_date, self.end_time)

	def is_single(self):
		return not self.repeat_period

	def is_finite(self):
		return bool(self.repeat_period and self.end_date)

	def is_ongoing(self):
		return bool(self.repeat_period and not self.end_date)

	def get_rrule_object(self, skip_time=False):
		start = self.start_date if skip_time else self.start
		end = self.end_date+timedelta(days=1) if self.end_date else None
		return rrule.rrule(self.repeat_period, dtstart=start, until=end, interval=self.repeat_every)

	def get_rule_conflicts(self, slot):
		"""
		Find conflicts between finite slot and finite or ongoing
		Returns exceptions list
		"""
		new_exceptions = []
		rule = slot.get_rrule_object()
		for rule_date in rule:
			if (rule_date.date() >= self.start_date
					and ((self.end_date and rule_date.date() <= self.end_date) or not self.end_date)
					and get_timestamp(rule_date.date()) not in slot.exceptions
					and self.is_rule_conflict(rule_date.date(), repeating=False)):
				new_exceptions.append(get_timestamp(rule_date.date()))
		return new_exceptions

	def get_exceptions_dict(self):
		ex_dict = dict([(ex, 1) for ex in self.exceptions])
		ex_dict['length'] = len(self.exceptions)
		return ex_dict

	def set_dates(self, start_dt, end_dt, set_end_date=False):
		start_date, start_time = get_date_minutes(start_dt)
		end_date, end_time = get_date_minutes(end_dt)

		self.start_date = start_date
		self.start_time = start_time
		self.end_time = end_time if end_time > 0 else 1440
		if set_end_date:
			self.end_date = end_date

	def __unicode__(self):
		return "Start: %s End: %s" % (self.start, self.end)

	def shift_exceptions(self, date_old, date_new):
		if self.repeat_period and len(self.exceptions) > 0 and date_old != date_new:
			shift_value = total_seconds(date_new-date_old)
			self.exceptions = [ex + shift_value for ex in self.exceptions]

	def is_rule_conflict(self, start_date, repeating):
		"""
		Find start_date intersection with rule
		repeating - if start_date single check exceptions
		"""
		if not repeating and (start_date < self.start_date or (self.end_date and start_date > self.end_date)):
			return False

		is_conflict = False
		repeat_every = self.repeat_every
		if self.repeat_period == rrule.WEEKLY:
			repeat_every *= 7
		dates_diff = start_date - self.start_date
		if (dates_diff.days % repeat_every) == 0:
			is_conflict = True

		if not repeating and is_conflict and get_timestamp(start_date) in self.exceptions:
			is_conflict = False

		return is_conflict

	@classmethod
	def check_for_conflicts(cls, healer, start_dt, end_dt, repeating=False, timeslot_object=None, timeslot_types=[]):
		"""
		Find conflicts with timeslots
		start_dt, end_dt - datetime range for checking
		repeating - is datetime range repeats or single
		timeslot_object - object for exclude from conflicts checking
		timeslot_types - list of timeslot types for checking
		"""

		start_date, start_time = get_date_minutes(start_dt)
		end_date, end_time = get_date_minutes(end_dt)
		exclude_time = Q(end_time__lte=start_time) | Q(start_time__gte=end_time)
		exclude_object = None
		qs_list = {"appointment": Appointment.objects.filter(healer=healer, confirmed=True).filter_by_date(start_date),
					"healertimeslot": HealerTimeslot.objects.filter(healer=healer).filter_by_date(start_date),
					"vacation": Vacation.objects.filter(healer=healer).filter_by_date(start_date)}

		for qs_type, qs in qs_list.iteritems():
			if timeslot_types and qs_type not in timeslot_types:
				continue

			if timeslot_object and type(timeslot_object) == qs.model:
				exclude_object = Q(id=timeslot_object.id)
			if qs_type != "vacation":
				exclude_query = exclude_time
				if exclude_object:
					exclude_query |= exclude_object
				qs = qs.exclude(exclude_query)
			elif exclude_object:
				qs = qs.exclude(exclude_object)

			for slot in qs:
				if repeating:
					# for single slot conflicts solved in browser
					if slot.repeat_period:
						if slot.is_rule_conflict(start_date, repeating):
							return True
				else:
					if slot.repeat_period and slot.is_rule_conflict(start_date, repeating):
						return True
					# check single slot
					if slot.is_single() and slot.start_date <= start_date and slot.end_date >= start_date:
						return True

		return False

	def find_conflicts(self, timeslots_query):
		"""
		Find conflicts with other timeslot.
		Returns result_code, exceptions list and conflicting slots.
		result_code:
			0 - success
			1 - conflict finite or ongoing with ongoing
			2 - conflict finite with single or finite
			3 - conflict single with others
		"""
		result_code = 0
		exceptions = []
		conflicting_slots = []
		exclude_query = Q(end_time__lte=self.start_time) | Q(start_time__gte=self.end_time)
		possible_conflicting_slots = timeslots_query.filter_by_date(self.start_date).exclude(exclude_query)
		if self.id:
			possible_conflicting_slots = possible_conflicting_slots.exclude(id=self.id)

		for slot in possible_conflicting_slots:
			if self.is_single():
				# check single conflicts
				if slot.is_single():
					if slot.start_date == self.start_date:
						conflicting_slots.append(slot)
						result_code = 3
						continue
				elif slot.is_rule_conflict(self.start_date, repeating=False):
					conflicting_slots.append(slot)
					result_code = 3
					continue

			if self.is_finite():
				#check finite conflicts
				if slot.is_ongoing():
					ongoing_exceptions = slot.get_rule_conflicts(self)
					exceptions.extend(ongoing_exceptions)
					if len(ongoing_exceptions) > 0:
						result_code = 1
						conflicting_slots.append(slot)
						break
				if slot.is_finite():
					rule_exceptions = slot.get_rule_conflicts(self)
					if rule_exceptions:
						result_code = 2
						exceptions.extend(rule_exceptions)
						conflicting_slots.append(slot)
				if slot.is_single():
					if self.is_rule_conflict(slot.start_date, repeating=False):
						result_code = 2
						exceptions.append(get_timestamp(slot.start_date))
						conflicting_slots.append(slot)

			if self.is_ongoing():
				#ongoing
				#check with ongoing
				if slot.is_ongoing():
					if (max(slot.repeat_every, self.repeat_every) % min(slot.repeat_every, self.repeat_every)) != 0:
						result_code = 1
						exceptions.append(get_timestamp(slot.start_date))
						conflicting_slots.append(slot)
						break
					if slot.is_rule_conflict(self.start_date, repeating=True):
						result_code = 1
						exceptions.append(get_timestamp(slot.start_date))
						conflicting_slots.append(slot)
						break
				#check with finite
				if slot.is_finite():
					rule_exceptions = self.get_rule_conflicts(slot)
					if rule_exceptions:
						exceptions.extend(self.get_rule_conflicts(slot))
						conflicting_slots.append(slot)
				#check with single
				if slot.is_single():
					if self.is_rule_conflict(slot.start_date, repeating=False):
						exceptions.append(get_timestamp(slot.start_date))
						conflicting_slots.append(slot)

		exceptions = list(set(exceptions))
		exceptions.sort()

		return result_code, exceptions, conflicting_slots

	def find_next_in_rule(self, start_dt):
		"""
		Returns next date in rule and count of skipped exceptions
		"""
		rule = rrule.rrule(self.repeat_period, dtstart=self.start_date, interval=self.repeat_every)
		next_start = rule.after(start_dt)
		skip = 0
		while get_timestamp(next_start.date()) in self.exceptions:
			next_start = rule.after(next_start)
			skip += 1
		return next_start.date(), skip

	def find_before_date_in_rule(self, end_dt):
		"""
		Returns last date in rule and count of skipped exceptions
		"""
		rule = rrule.rrule(self.repeat_period, dtstart=self.start_date, interval=self.repeat_every)
		end_dt = rule.before(datetime.combine(end_dt.date(), time()))
		skip = 0
		while get_timestamp(end_dt.date()) in self.exceptions:
			end_dt = rule.before(end_dt)
			skip += 1
		return end_dt.date(), skip

	def count_repeats_in_rule(self, until):
		rule = rrule.rrule(self.repeat_period, dtstart=self.start_date, until=until, interval=self.repeat_every)
		return rule.count()

	def check_last_in_rule(self):
		if self.end_date and (self.count_repeats_in_rule(self.end_date) - len(self.exceptions)) <= 1:
			self.repeat_period = None
			self.end_date = self.start_date
			self.exceptions = []

	def convert_to_single(self, start_old_dt, start_new_dt, end_new_dt):
		single_timeslot = deepcopy(self)
		single_timeslot.set_dates(start_new_dt, end_new_dt)
		single_timeslot.repeat_period = None
		single_timeslot.end_date = single_timeslot.start_date
		single_timeslot.exceptions = []
		single_timeslot.id = None
		single_timeslot.save()

		update_first_item = self.start_date == start_old_dt.date()
		if update_first_item:
			self.start_date, skip = self.find_next_in_rule(start_old_dt)
		else:
			self.exceptions.append(get_timestamp(start_old_dt.date()))
		self.check_last_in_rule()
		self.save()

		return single_timeslot, self

	def delete_single(self, start_dt):
		if self.start_date == start_dt.date():
			self.start_date, skip = self.find_next_in_rule(start_dt)
		else:
			self.exceptions.append(get_timestamp(start_dt.date()))
		self.check_last_in_rule()
		self.save()

	@classmethod
	def group_by_date(cls, timeslots):
		""" Groups timeslots by start date """
		groups = {}
		for key, group in groupby(timeslots, key=lambda o: o.start.strftime("%d%m%y")):
			groups[key] = list(group)
		return groups

	@classmethod
	def prepare_json_slots(cls, keys, data):
		joined_data = []
		for value in data:
			joined_data.extend(value)
		slotList = {
			'keys': keys,
			'data': joined_data
		}
		return slotList

	def date_range_text(self):
		return date_range_text(self.start, self.end)

	def date_text(self):
		return self.start.strftime("%A - %B %d")

	def time_range_text(self):
		if self.end.hour == 0 and self.end.minute == 0:
			second_part = ' - 24:00 pm'
		else:
			second_part = ' - %d:%02d %s' % (self.end.hour, self.end.minute, self.end.strftime('%p').lower())
		return '%d:%02d %s' % (self.start.hour, self.start.minute, second_part)

	def week(self):
		return self.start_date.strftime("%U")

	class Meta:
		abstract = True


class HealerTimeslot(Timeslot):
	healer = models.ForeignKey(Healer)
	location = models.ForeignKey(Location, null=True, default=None)

	def as_dict(self):
		slot = {'start_date': self.start_date.isoformat(),
				'start_time': self.start_time,
				'end_time': self.end_time,
				'end_date': self.end_date.isoformat() if self.end_date else 0,
				'slot_id': self.id,
				'location': self.location.id if self.location else -1,
				'location_title': Location.get_name(self),
				'repeat_every': self.repeat_every,
				'repeat_period': self.repeat_period if self.repeat_period else 0,
				'exceptions': self.get_exceptions_dict(),
				'setup_time': self.healer.setup_time,
				'healer_name': self.healer.user.get_full_name(),
				'healer_username': self.healer.user.username}
		return slot

	def json_object(self):
		return json.dumps(self.as_dict())

	def __unicode__(self):
		return "Healer: %s Start: %s End: %s" % (self.healer, self.start, self.end)

	def set_weekly(self, weekly, end_date=None):
		if weekly:
			self.repeat_period = rrule.WEEKLY
			if not end_date:
				if not self.id:  # ongoing from current week for new slot
					weeks = (self.start_date - self.healer.get_local_time().date()).days / 7
					if weeks:
						self.start_date -= timedelta(weeks=weeks)

				self.end_date = None
			else:
				self.end_date = end_date
				self.check_last_in_rule()
		else:
			self.end_date = self.start_date
			self.repeat_period = None


class AppointmentConflict(Exception):
	def __init__(self, value=""):
		self.value = value

	def __str__(self):
		return repr(self.value)


class AppointmentManager(TimeslotManager):
	def get_queryset(self):
		qs = super(AppointmentManager, self).get_queryset().filter(canceled=False)
		qs = qs.select_related('client', 'healer', 'location', 'client__user', 'treatment_length')
		return qs

	def without_relations(self):
		qs = super(AppointmentManager, self).get_queryset().filter(canceled=False)
		return qs

	def get_active(self, healer, healers=None):
		"""
		Get started from today or repeating not ended yet, exclude from not approved clients
		"""
		qs = self.get_queryset()
		if healers is not None:
			qs = qs.filter(healer__in=healers)
		else:
			qs = qs.filter(healer__id=healer.id)
		qs = qs.filter_by_date(healer.get_local_time().date())
#		qs = qs.exclude(client__user__is_active=False, client__approval_rating=0)
		qs = qs.order_by('start_date')
		return qs

	def get_active_json(self, healer):
		appts = Appointment.objects.get_active(healer)

		data = [[a.start.isoformat(), a.end.isoformat(),
				a.end_date.isoformat() if a.end_date else 0,
				a.treatment_length.id,
				a.id, 0,
				str(a.client) + (" (%d)" % a.client.approval_rating if not a.confirmed else ""),
				str(a.client.user.username),
				(a.location.id if a.location is not None else -1),
				(str(a.location) if a.location is not None else "Unspecified"),
				(a.repeat_every if a.repeat_every else 0),
				(a.repeat_period if a.repeat_period is not None else 0),
				(a.repeat_count if a.repeat_count is not None else 0),
				a.get_exceptions_dict(),
				(1 if a.confirmed else 0),
				str(a.note)] for a in appts]
		keys = ["start", "end", "end_date", "treatment_length",
				"slot_id", "readOnly", "client_name", "client", "location", "location_title",
				"repeat_every", "repeat_period", "repeat_count", "exceptions", "confirmed", "note"]

		return Timeslot.prepare_json_slots(keys, data)

	def estimate_number(self, client_users, healer):
		"""
		Calculate number of appointments before date for clients
		"""
		now = settings.GET_NOW().date()
		appts = Appointment.objects.filter(client__user__in=client_users, healer=healer).before_date(now)
		appts_count = {}
		for appt in appts:
			if not appt.client.user in appts_count:
				appts_count[appt.client.user] = 0
			if appt.is_single():
				appts_count[appt.client.user] += 1
			else:
				end_date = appt.end_date if appt.is_finite() and appt.end_date<now else now
				if appt.repeat_period == rrule.DAILY:
					appts_count[appt.client.user] += (end_date - appt.start_date).days
				if appt.repeat_period == rrule.WEEKLY:
					appts_count[appt.client.user] += (end_date - appt.start_date).days/7
		return appts_count


class CanceledAppointmentManager(models.Manager):
	def get_queryset(self):
		return super(CanceledAppointmentManager, self).get_queryset().filter(canceled=True)


class DiscountCode(models.Model):
	TYPE_CHOICES = ('$', '%')

	healer = models.ForeignKey(Healer, related_name="discount_codes")
	code = models.CharField(max_length=30)
	amount = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
		MaxValueValidator(1000)])
	type = models.CharField(max_length=1, choices=[(c, c) for c in TYPE_CHOICES], default='$')
	remaining_uses = models.PositiveSmallIntegerField(blank=True, null=True)
	is_gift_certificate = models.BooleanField(default=False)

	class Meta:
		ordering = ['code']
		unique_together = ('healer', 'code')

	def __unicode__(self):
		return '%s - %d%s' % (self.code, self.amount, self.type)


class GiftCertificate(models.Model):
	purchased_for = models.CharField(max_length=100)
	purchased_by = models.CharField(max_length=100)
	discount_code = models.ForeignKey(DiscountCode)
	purchase_date = models.DateField(auto_now_add=True)
	redeemed = models.BooleanField(default=False)
	message = models.TextField(max_length=255, default='', blank=True)

	class Meta:
		ordering = ['purchased_for']

	def __unicode__(self):
		return '%s - %s' % (self.purchased_by, self.discount_code)

	def description(self):
		return 'Gift Certificate Purchase - %s - %s' % (self.purchased_by, self.discount_code.code)

	def expiry_date(self):
		healer = self.discount_code.healer
		type = Healer.GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_LABELS[healer.gift_certificates_expiration_period_type]
		params = {type: healer.gift_certificates_expiration_period}
		return self.purchase_date + relativedelta(**params)

	def redeem(self):
		if not self.redeemed:
			self.discount_code.remaining_uses = 0
			self.discount_code.save()
			self.redeemed = True
			self.save()

	def is_expired(self):
		return date.today() > self.expiry_date()


def get_appointment_cost(treatment_length, discount_code):
	if not treatment_length:
		return 0
	try:
		cost = float(treatment_length.cost)
	except ValueError:
		return 0
	if discount_code is not None:
		if discount_code.type == '$':
			cost -= discount_code.amount
		else:
			cost -= cost * discount_code.amount / 100.0
	if cost < 0:
		return 0
	if int(cost) == cost:
		return float(cost)
	else:
		return round(cost, 2)


class Appointment(Timeslot):
	healer = models.ForeignKey(Healer, related_name='healer_appointments')
	client = models.ForeignKey(Client)
	location = models.ForeignKey(Location, null=True, default=None)
	room = models.ForeignKey(Room, null=True, default=None)
	treatment_length = models.ForeignKey(TreatmentTypeLength, null=True, default=None)  # None - Custom
	note = models.TextField(null=True, blank=True, default='')

	canceled = models.BooleanField(default=False)
	confirmed = models.BooleanField(default=True)

	repeat_count = models.PositiveIntegerField(default=0, null=True)

	google_event_id = models.CharField(max_length=1024, blank=True)

	base_appointment = models.ForeignKey('self', null=True, default=None)

	created_by = models.ForeignKey(User, related_name="created_appts")
	created_date = models.DateTimeField()
	last_modified_by = models.ForeignKey(User, related_name="modified_appts")
	last_modified_date = models.DateTimeField()
	discount_code = models.ForeignKey(DiscountCode, null=True, blank=True)

	objects = AppointmentManager()
	canceled_objects = CanceledAppointmentManager()
	all_objects = models.Manager()

	def treatment_type_name(self):
		if self.treatment_length is None:
			return 'Custom'
		else:
			return self.treatment_length.treatment_type.title

	def treatment_type_length_name(self):
		if self.treatment_length is None:
			return 'Custom'
		else:
			return self.treatment_length.title()

	def cost(self):
		return get_appointment_cost(self.treatment_length, self.discount_code)

	def unpaid(self):
		unpaid = self.cost() - self.paid()
		if unpaid < 0:
			unpaid = 0
		return unpaid

	def paid(self):
		payments = self.payments.filter(date=self.start_date)
		if payments.exists():
			return payments.aggregate(sum=models.Sum('amount'))['sum'] / 100.0
		else:
			return 0

	def is_marked_paid(self):
		return self.payments.filter(date=self.start_date, paid=True).exists()

	def is_paid_with_card(self):
		return self.unpaid() == 0

	def is_paid(self):
		return self.is_paid_with_card() or self.is_marked_paid()

	def mark_paid(self):
		if not self.is_marked_paid():
			payment = Payment.objects.get_or_create(appointment=self, date=self.start_date, amount=0)[0]
			payment.paid = True
			payment.save()

	def mark_unpaid(self):
		self.payments.filter(date=self.start_date, paid=True).delete()

	def is_finite(self):
		return bool(self.repeat_period and self.repeat_count)

	def is_ongoing(self):
		return bool(self.repeat_period and not self.repeat_count)

	def repeat_exact_count(self):
		if not self.repeat_count:
			raise Exception

		return self.repeat_count - len(self.exceptions)

	def timezone(self, remove_separator=False):
		if self.location and self.location.timezone:
			if remove_separator:
				return self.location.timezone.replace(':', '')
			else:
				return self.location.timezone
		return ''

	def owner_healer(self):
		if self.location is not None:
			return self.location.healer
		return self.healer

	def owner_healer_has_intake_form(self):
		return self.owner_healer().has_intake_form()

	def client_completed_form(self):
		return self.owner_healer().completed_forms().filter(client=self.client).exists()

	def healer_has_notes_for_client(self):
		return self.healer.notes.filter(client=self.client).exists()

	def owner_healer_has_notes_for_client(self):
		return self.owner_healer().notes.filter(client=self.client).exists()

	def as_dict(self):
		appt = {'start_date': self.start_date.isoformat(),
				'start_time': self.start_time,
				'end_time': self.end_time,
				'end_date': self.end_date.isoformat() if self.end_date else 0,
				'slot_id': self.id,
				'readOnly': 0,
				'client_name': str(self.client),
				'client': str(self.client.user.username),
				'client_id': self.client.id,
				'client_has_email': 1 if self.client.user.email else 0,
				'location': self.location.id if self.location else -1,
				'location_title': Location.get_name(self),
				'treatment_length': self.treatment_length.id if self.treatment_length else 0,
				'cost': self.cost(),
				'room': self.room.id if self.room is not None else 0,
				'room_name': self.room.name if self.room is not None else '',
				'discount_code': self.discount_code.pk if self.discount_code is not None else '',
				'repeat_every': self.repeat_every,
				'repeat_period': self.repeat_period if self.repeat_period else 0,
				'repeat_count': self.repeat_count if self.repeat_count else 0,
				'exceptions': self.get_exceptions_dict(),
				'confirmed': 1 if self.confirmed else 0,
				'note': self.note,
				'setup_time': self.healer.setup_time,
				'healer_name': self.healer.user.get_full_name(),
				'healer_username': self.healer.user.username,
				'intake': self.client_completed_form(),
				'has_intake': self.owner_healer_has_intake_form(),
				'healer_has_notes_for_client': self.healer_has_notes_for_client(),
				'owner_healer_has_notes_for_client': self.owner_healer_has_notes_for_client()}
		return appt

	def json_object(self):
		return json.dumps(self.as_dict())

	def update_end_date(self):
		if self.is_single():
			self.end_date = self.start_date
		elif self.is_ongoing():
			self.end_date = None
		elif self.is_finite():
			rule = self.get_rrule_object()
			self.end_date = rule[-1].date()

	def get_rrule_object(self, skip_time=False):
		count = None if (not self.repeat_count or self.repeat_count == 0) else self.repeat_count
		start = self.start_date if skip_time else self.start
		return rrule.rrule(self.repeat_period, dtstart=start, interval=self.repeat_every, count=count)

	@classmethod
	def generate_recurrency(cls, appts, start, end, reverse_sort=False,
			skip_date_filter=False, only_unpaid=False, only_confirmed=False):
		def appointments_filter(appt):
			if appt.start_date < start.date():
				return False
			if only_unpaid:
				if appt.is_paid():
					return False
			if only_confirmed:
				if not appt.confirmed:
					return False
			return True

		new_appts = []
		for appt in appts:
			if appt.repeat_period:
				rule = appt.get_rrule_object()
				for rule_date in rule.between(start, end):
					if rule_date.date() != appt.start_date and get_timestamp(rule_date.date()) not in appt.exceptions:
						new_appt = deepcopy(appt)
						new_appt.start_date = rule_date.date()
						new_appts.append(new_appt)
		if len(new_appts) > 0:
			appts = list(appts)
			appts.extend(new_appts)
			appts = sorted(appts, key=lambda appt: appt.start, reverse=reverse_sort)

		if skip_date_filter:
			return appts

		return filter(appointments_filter, appts)

	@classmethod
	def get_appointments(cls, user, number_of_days, client=None,
							start_date=None, end_date=None, only_unpaid=False):
		def get_wcenter_appointments():
			providers = healers.utils.get_healers_in_wcenter_with_schedule_editing_perm(healer)
			return cls.objects.filter(healer__in=providers,
				location__in=healers.utils.get_wcenter_location_ids(healer.user)).order_by('healer')

		healer = get_object_or_404(Healer, user=user)

		if end_date is None:
			end = healer.get_local_day()
		else:
			end = datetime(
				year=end_date.year,
				month=end_date.month,
				day=end_date.day,
			)

		if start_date is None:
			start = end - timedelta(days=number_of_days)
		else:
			start = datetime(
				year=start_date.year,
				month=start_date.month,
				day=start_date.day,
			)

		if is_wellness_center(healer):
			appts = get_wcenter_appointments()
		else:
			appts = cls.objects.filter(healer=healer)
		if client is not None:
			appts = appts.filter(client=client)
		appts = appts.filter_by_date(start=start, end=end).order_by('-start_date', '-start_time')
		appts = cls.generate_recurrency(appts, start, end, reverse_sort=True,
			only_unpaid=only_unpaid, only_confirmed=True)
		return appts

	def recurrency_string(self):
		if self.repeat_period:
			repeat_period = dict(Appointment.REPEAT_CHOICES)[self.repeat_period]
			return "Repeats every %d %s%s" % (self.repeat_every,
												repeat_period,
												pluralize(self.repeat_every))
		return ""

	def get_rule_conflicts(self, slot):
		"""
		Find conflicts between finite slot and finite or ongoing
		Returns exceptions list
		"""
		new_exceptions = []
		rule = slot.get_rrule_object()
		for rule_date in rule:
			if rule_date.date()>=self.start_date \
					and ((self.end_date and rule_date.date()<=self.end_date) or not self.end_date) \
					and get_timestamp(rule_date.date()) not in slot.exceptions\
					and self.is_rule_conflict(rule_date.date(), repeating=False):
				new_exceptions.append(get_timestamp(rule_date.date()))
		return new_exceptions

	def find_available_dates(self, number_of_dates):
		"""
		Find available dates for finite slot after it's end date
		Find interval is limited with number_of_dates*4 repeats
		If conflicts, returns None
		"""
		available_dates = []
		rule = rrule.rrule(self.repeat_period, dtstart=self.end_date,
						   interval=self.repeat_every, count=number_of_dates*4)
		ruleset = rrule.rruleset()
		ruleset.rrule(rule)
		ruleset.exdate(datetime.combine(self.end_date, time()))

		exclude_query = Q(end_time__lte=self.start_time) | Q(start_time__gte=self.end_time) | Q(id=self.id)
		conflict_slots = Appointment.objects.filter(healer=self.healer, confirmed=True).\
												filter_by_date(self.end_date).\
												exclude(exclude_query)

		exdates = []
		if len(conflict_slots):
			from_date = rule[1]
			to_date = rule[-1]
			for slot in conflict_slots:
				if slot.is_single():
					exdates.append(datetime.combine(slot.start_date, time()))
				else:
					exruleset = rrule.rruleset()
					exruleset.rrule(slot.get_rrule_object(skip_time=True))
					for timestamp in slot.exceptions:
						exruleset.exdate(datetime.utcfromtimestamp(timestamp))
					exdates.extend(exruleset.between(from_date, to_date, inc=True))

		repeat_count = 0
		exceptions = []
		for rule_date in ruleset:
			repeat_count += 1
			if rule_date not in exdates:
				available_dates.append(rule_date)
				if len(available_dates) == number_of_dates:
					break
			else:
				exceptions.append(get_timestamp(rule_date))

		if len(available_dates)==number_of_dates:
			return {
				'dates': available_dates,
				'exceptions': exceptions,
				'repeat_count': repeat_count
			}

	def reschedule_conflicts(self, exceptions):
		available_dates = self.find_available_dates(len(exceptions))
		if not available_dates:
			return False

		if not self.repeat_count:
			raise Exception

		self.repeat_count += available_dates['repeat_count']
		self.exceptions.extend(available_dates['exceptions'])
		self.update_end_date()
		return True

	@classmethod
	def create_new(cls, healer_user_id, client_id, location_id, start, end,
		creator_user, treatment_length, room_id, repeat_period=None,
		repeat_every=1, repeat_count=0, conflict_solving=0, note='',
		notify_client=True, creator=None, check_for_conflicts=False,
		discount_code=None):

		def get_confirmed():
			if not creator_user.id == healer.user.id and not wcenter_control:
				if creator_user.id:
					return Appointment.check_for_auto_confirm(healer, client)
				else:
					return False
			return True

		try:
			location = Location.objects.get(id=location_id)
		except Location.DoesNotExist:
			location = None

		try:
			room = healers.utils.check_room(room_id, location_id, treatment_length)
		except Exception as e:
			if check_for_conflicts:
				return False
			return str(e), 4, None, None

		healer = get_object_or_404(Healer, user__id=healer_user_id)
		client = get_object_or_404(Client, id=client_id)
		wcenter_control = wcenter_get_provider(creator_user, healer.user.username)
		confirmed = get_confirmed()

		appt = Appointment(healer = healer,
						   client = client,
						   location = location,
						   room = room,
						   treatment_length = treatment_length,
						   confirmed = confirmed,
						   repeat_period = repeat_period,
						   repeat_every = repeat_every,
						   repeat_count = repeat_count,
						   note=note,
						   created_by=creator,
						   created_date=settings.GET_NOW(),
						   last_modified_by=creator,
						   discount_code=discount_code)
		appt.set_dates(start, end)
		appt.update_end_date()

		result_code, exceptions, conflicting_slots = appt.find_conflicts(
			cls.get_possible_conflict_appts(healer, room))

		if check_for_conflicts:
			return result_code == 0  # no conflicts

		if conflict_solving > 0:
			result_code = 0

		if result_code == 0:
			if not appt.is_single():
				appt.exceptions = exceptions
				if conflict_solving == 2:
					if not appt.reschedule_conflicts(exceptions):
						# show form againg without reschedule option
						result_code = 2
						return appt, result_code, exceptions, []
			appt.save()
			appt.cancel_conflicting_unconfirmed_appointments()

			from_user = creator_user if creator_user.id else client.user
			if confirmed and notify_client:
				if wcenter_control:
					appt.notify_created(client.user)
					appt.notify_created(creator_user)
				else:
					appt.notify_created(from_user)
			elif confirmed and not notify_client:
				appt.notify_created(client.user)
			else:
				appt.notify_requested(from_user)

		available_dates = []
		if result_code == 2:
			available_dates_dict = appt.find_available_dates(len(exceptions))
			if available_dates_dict:
				available_dates = available_dates_dict['dates']
			else:
				result_code = 1

		return appt, result_code, exceptions, available_dates

	def check_first_instance_dates(self, start_delta, end_delta):
		today = self.healer.get_local_time().date()
		if not self.is_single() and self.start_date>=today:
			new_start = self.start + start_delta
			if new_start.date()<today:
				return False
		return True

	def is_data_changed(self, start_delta, end_delta, treatment_length, location, discount_code):
		if (not start_delta and
			not end_delta and
			self.treatment_length == treatment_length and
			self.location == location and
			self.discount_code == discount_code):
			return False
		return True

	def correct_dates_by_exceptions(self):
		if not self.is_finite():
			return
		if get_timestamp(self.start_date) in self.exceptions:
			self.start_date, skip = self.find_next_in_rule(self.start)
			self.repeat_count -= 1 + skip
		if get_timestamp(self.end_date) in self.exceptions:
			self.end_date, skip = self.find_before_date_in_rule(datetime.combine(self.end_date, time()))
			self.repeat_count -= 1 + skip

	@classmethod
	def get_possible_conflict_appts(cls, healer, room):
		possible_conflict_appts = Appointment.objects.filter(canceled=False)
		if room:
			possible_conflict_appts = possible_conflict_appts.filter(
				Q(healer=healer) | Q(room=room))
		else:
			possible_conflict_appts = possible_conflict_appts.filter(
				confirmed=True, healer=healer)
		return possible_conflict_appts

	def update(self, start_delta, end_delta, treatment_length, location, room,
				note, conflict_solving=0, client=None, discount_code=False):
		self.split_on_past()

		start_old = self.start_date
		self.set_dates(self.start+start_delta, self.end+end_delta)
		self.update_end_date()
		self.location = location
		self.room = room
		if client is not None:
			self.client = client

		if discount_code is not False:
			self.discount_code = discount_code
		self.note = note
		self.treatment_length = treatment_length
		if not self.is_single():
			self.shift_exceptions(start_old, self.start_date)

		result_code, exceptions, conflicting_slots = self.find_conflicts(
			Appointment.get_possible_conflict_appts(self.healer, room))

		if conflict_solving > 0:
			result_code = 0

		if result_code == 0:
			if not self.is_single() and exceptions:
				self.exceptions.extend(exceptions)
				if conflict_solving == 2:
					if not self.reschedule_conflicts(exceptions):
						# show form againg without reschedule option
						result_code = 2
						return result_code, exceptions, []
				self.correct_dates_by_exceptions()

			self.save()
			self.cancel_conflicting_unconfirmed_appointments()

		available_dates = []
		if result_code == 2:
			available_dates_dict = self.find_available_dates(len(exceptions))
			if available_dates_dict:
				available_dates = available_dates_dict['dates']
			else:
				result_code = 1

		return result_code, exceptions, available_dates

	def convert_to_single(self, start_old_dt, start_new_dt, end_new_dt):
		single_timeslot = deepcopy(self)
		single_timeslot.set_dates(start_new_dt, end_new_dt)
		single_timeslot.repeat_period = None
		single_timeslot.repeat_count = 0
		single_timeslot.end_date = single_timeslot.start_date
		single_timeslot.exceptions = []
		single_timeslot.google_event_id = ''

		result_code, exceptions, conflicting_slots = single_timeslot.find_conflicts(Appointment.objects.filter(healer=self.healer, confirmed=True))
		if result_code>0:
			raise AppointmentConflict()

		update_first_item = self.start_date == start_old_dt.date()
		update_last_item = self.is_finite() and self.end_date == start_old_dt.date()
		if update_first_item:
			self.start_date, skip = self.find_next_in_rule(start_old_dt)
			if self.repeat_count:
				self.repeat_count -= 1 + skip

				if self.repeat_exact_count() <= 1:
					self.canceled = True
		elif update_last_item:
			self.end_date, skip = self.find_before_date_in_rule(start_old_dt)
			self.repeat_count -= 1 + skip
		else:
			self.exceptions.append(get_timestamp(start_old_dt.date()))
		self.save()

		single_timeslot.id = None
		single_timeslot.base_appointment = self
		single_timeslot.save()

		return single_timeslot, self

	def split_on_past(self, dt=None):
		""" Splits appointment on before dt and current """
		if not dt:
			dt = self.healer.get_local_time()
		if self.start_date < dt.date():
			end_date, exceptions = self.find_before_date_in_rule(dt)
			past_timeslot = deepcopy(self)
			past_timeslot.id = None
			past_timeslot.end_date = end_date
			if past_timeslot.start_date == past_timeslot.end_date:
				past_timeslot.repeat_period = None
				past_timeslot.repeat_count = 0
				past_timeslot.exceptions = []
			else:
				if self.repeat_count:
					self.repeat_count -= self.count_repeats_in_rule(past_timeslot.end_date)
					past_timeslot.repeat_count -= self.repeat_count
				else:
					past_timeslot.repeat_count = self.count_repeats_in_rule(past_timeslot.end_date)
			past_timeslot.save()

			self.start_date, skip = self.find_next_in_rule(dt - timedelta(days=1))
			if self.start_date == self.end_date:
				self.repeat_period = None
				self.repeat_count = 0
				self.exceptions = []
			if not self.base_appointment:
				self.base_appointment = past_timeslot
			return past_timeslot

	@classmethod
	def check_for_auto_confirm(cls, healer, client):
		# for dummy users always unconfirmed
		if healer.manualAppointmentConfirmation == Healer.CONFIRM_AUTO:
			return True

		if healer.manualAppointmentConfirmation == Healer.CONFIRM_MANUAL:
			return False

		if healer.manualAppointmentConfirmation == Healer.CONFIRM_MANUAL_NEW:
			if not client or not client.user.is_active:
				return False
			else:
				return is_my_client(healer.user, client.user)

	def confirm(self):
		self.confirmed = True
		self.last_modified_by = self.healer.user
		self.save(confirming=True)

		self.notify_confirmed(self.healer.user)

		self.cancel_conflicting_unconfirmed_appointments()

		if self.client.approval_rating==0:
			self.client.approval_rating = 100
			self.client.save()

	def cancel_conflicting_unconfirmed_appointments(self):
		if self.confirmed:
			# repeating unconfirmed appts not existing
			other_appts = self.find_conflicts(Appointment.objects.filter(healer=self.healer, confirmed=False, repeat_period__isnull=True))[2]
			for other_appt in other_appts:
				other_appt.cancel(self.healer.user)
				other_appt.notify_declined(self.healer.user)

	def cancel(self, modified_by):
		self.canceled = True
		self.last_modified_by = modified_by
		self.save(cancel=True)

	def cancel_single(self, start_dt):
		remove_first_item = self.start_date == start_dt.date()
		remove_last_item = self.is_finite() and self.end_date == start_dt.date()
		if remove_first_item:
			# first is last
			if self.repeat_count and self.repeat_exact_count() <= 1:
				self.cancel(self.healer.user)
				return self, self
			else:
				self.start_date, skip = self.find_next_in_rule(start_dt)
				if self.repeat_count:
					self.repeat_count -= 1 + skip
				self.save()
		elif remove_last_item:
			self.end_date, skip = self.find_before_date_in_rule(start_dt)
			self.repeat_count -= 1 + skip
			self.save()
		else:
			self.exceptions.append(get_timestamp(start_dt.date()))
			self.save()
		base_appointment_id = self.id

		# save new instance as canceled
		canceled_appt = deepcopy(self)
		canceled_appt.id = None
		canceled_appt.start_date = start_dt.date()
		canceled_appt.end_date = start_dt.date()
		canceled_appt.repeat_period = None
		canceled_appt.canceled = True
		canceled_appt.base_appointment_id = base_appointment_id
		canceled_appt.save()

		return self, canceled_appt

	def notify_created(self, from_user):
		self.notify(from_user, 'created')

	def notify_requested(self, from_user):
		self.notify(from_user, 'requested')
		if self.healer.send_sms_appt_request and self.healer.user != from_user:
			self.notify_sms(from_user)

	def notify_updated(self, from_user, previous_dates, is_wcenter):
		self.notify(from_user, 'updated', previous_dates, is_wcenter=is_wcenter)

	def notify_canceled(self, from_user, is_wcenter=False, notify_client=True):
		self.notify(from_user, 'canceled', is_wcenter=is_wcenter, notify_client=notify_client)

	def notify_confirmed(self, from_user):
		admin_copy = getattr(settings, 'COPY_ADMIN_CONFIRMATION', False)
		self.notify(from_user, 'confirmed', admin_copy=admin_copy)

	def notify_declined(self, from_user):
		self.notify(from_user, 'declined')

	def send_reminder(self, from_user):
		admin_copy = getattr(settings, 'COPY_ADMIN_REMINDER', False)
		self.notify(from_user, 'reminder', admin_copy=admin_copy)

	def event_info(self):
		lines = ['Room: %s' % self.room]
		if self.treatment_length:
			lines.append("Treatment Type: %s" % self.treatment_length.full_title())

		if self.client.user.email:
			lines.append("Contact email: %s" % self.client.user.email)

		phone = self.client.first_phone()
		if phone:
			lines.append("Contact phone: %s" % phone)

		if self.note:
			lines.append("Note: %s" % self.note)

		lines.append("Cancel appointment: %s" % absolute_url(reverse('healer_appointment_cancel', args=[self.pk])))

		return "\n".join(lines)

	def plain_text(self):
		""" Returns plain text with description of appointment """
		lines = ["%s" % self.date_range_text()]
		if self.repeat_period:
			lines.append(self.recurrency_string())
		if self.location:
			lines.append("\nLocation: \n\t%s" % self.location.full_address_text())
		if self.treatment_length:
			lines.append("\nTreatment Type: \n\t%s" % self.treatment_length.treatment_type)
			lines.append("\nCost: \n\t$%s" % self.cost())
		else:
			lines.append("\nTreatment Type: \n\tCustom Treatment")
		if self.note:
			lines.append("\nNote: %s" % self.note)

		return "\n".join(lines)

	def notify_sms(self, from_user):
		to = self.healer.first_phone()
		if not to:
			return

		from_user_profile = from_user.client
		from_user_name = str(from_user_profile)
		ctx = {
			"from_user_name": from_user_name,
			"appointment": self
		}
		body = render_to_string('healers/emails/appointment_requested_sms.txt', ctx)
		send_sms(self.healer.first_phone(), body)

		if not self.confirmed:
			from healers.utils import get_full_url
			body = "To Confirm: %s\nTo Decline: %s" % (
					get_full_url("appointment_confirm", args=[self.id]),
					get_full_url("appointment_decline", args=[self.id])
				)
			send_sms(self.healer.first_phone(), body)

	def notify(self, from_user, action, previous_dates=None, admin_copy=False,
			is_wcenter=False, notify_client=True):
		""" Send notification message about appointment changes from healer to client and vice versa """
		def send_email(name=None):
			from healers.utils import get_full_url

			from_user_profile = from_user.client
			from_user_name = str(from_user_profile).decode('ascii', 'replace')
			confirm_url = decline_url = manage_url = None
			client_info = []
			cancellation_policy = None
			additional_text_for_email = None
			healer_link = None
			wcenter_control = wcenter_get_provider(from_user, self.healer.user.username)
			if self.healer.user == from_user or wcenter_control:
				# to client
				to_client = True
				to_user = self.client.user
				cancellation_policy = self.healer.cancellation_policy
				additional_text_for_email = self.healer.additional_text_for_email
				manage_url = get_full_url("receiving_appointments")
				healer_link = from_user_profile.healer.get_full_url()
			else:
				# to healer
				to_client = False
				to_user = self.healer.user
				if not self.confirmed:
					confirm_url = get_full_url("appointment_confirm", args=[self.id])
					decline_url = get_full_url("appointment_decline", args=[self.id])

				client_info.append(self.client.contact_info())

				if (not is_my_client(self.healer.user, from_user) and
						not is_wcenters_client(self.healer.user, from_user)):
					client_info.append("%s is a new Client" % from_user_name)
					if from_user_profile.referred_by:
						client_info.append("%s was referred by %s" %
							(from_user_name, from_user_profile.referred_by))

			to_email = to_user.email
			if not to_email:
				#try getting email from ContactInfo
				from contacts_hs.models import ContactEmail
				to_email = ContactEmail.objects.get_first_email(to_user)

				if not to_email:
					return

			ctx = {
				"SITE_NAME": settings.SITE_NAME,
				"CONTACT_EMAIL": settings.CONTACT_EMAIL,
				"from_user_name": from_user_name,
				"client_info": "\n".join(client_info) if client_info else None,
				"appointment": self,
				"action": action,
				"appointments_confirm_url": confirm_url,
				"appointments_decline_url": decline_url,
				"appointments_manage_url": manage_url,
				"cancellation_policy": cancellation_policy,
				"additional_text_for_email": additional_text_for_email,
				"healer_link": healer_link,
				'to_user_name': to_user.first_name,
				'to_client': to_client,
				'name': name or self.healer.user.client,
			}

			email_subject_template = 'healers/emails/appointment_subject.txt'
			if action == "reminder":
				email_subject_template = 'healers/emails/appointment_reminder_subject.txt'
				ctx['reminder_disable_link'] = get_full_url("disable_reminders")

			if previous_dates:
				ctx["previous_dates"] = date_range_text(previous_dates['start'], previous_dates['end'])

			from_email = settings.DEFAULT_FROM_EMAIL

			subject = render_to_string(email_subject_template, ctx)

			bcc = None
			if admin_copy:
				bcc = [admin[1] for admin in settings.ADMINS]

			from healers.utils import send_hs_mail
			send_hs_mail(subject, 'healers/emails/appointment_%s_message.txt' % action,
				ctx, from_email, [to_email], bcc=bcc)

		def get_name(user):
			return str(user.client).decode('ascii', 'replace')

		if is_wcenter:
			if action == 'canceled':
				# to client
				send_email()
				# to healer
				from_user = self.client.user
				send_email(name=get_name(from_user))
			elif action == 'updated':
				# to healer
				send_email(name=get_name(from_user))
				# to client
				from_user = self.healer.user
				send_email()
		else:
			if notify_client:
				send_email()

	def save(self, *args, **kwargs):
		def center_has_gcal():
			for wcenter in wcenters:
				if wcenter.google_calendar_id:
					return True
			return False

		is_new = self.id is None
		am_confirming = kwargs.pop('confirming', False)
		cancel = kwargs.pop('cancel', False)
		google_sync = kwargs.pop('google_sync', True)
		self.last_modified_date = settings.GET_NOW()
		wcenters = self.healer.get_wellness_centers()

		for wcenter in wcenters:
			if self.location.pk in wcenter.get_location_ids() and not is_my_client(wcenter.user, self.client.user):
				healers.utils.add_user_to_clients(wcenter.user, self.client.user)

		super(Appointment, self).save(*args, **kwargs)
		if google_sync and (not self.canceled or cancel) and self.confirmed:
			if (center_has_gcal() or self.healer.google_calendar_id):
				if cancel:
					action = ACTION_DELETE
				elif is_new or am_confirming:
					action = ACTION_NEW
				else:
					action = ACTION_UPDATE

				for wcenter in wcenters:
					if wcenter.google_calendar_id and self.location.pk in wcenter.get_location_ids():
						CalendarSyncQueueTask.objects.add(self, action, wcenter)

				if self.healer.google_calendar_id:
					CalendarSyncQueueTask.objects.add(self, action)

	def __unicode__(self):
		return "Healer: %s Client: %s Start: %s End: %s" % (self.healer, self. client, self.start, self.end)


class WellnessCenterGoogleEventId(models.Model):
	wellness_center = models.ForeignKey(WellnessCenter)
	appointment = models.ForeignKey(Appointment,
		related_name='wellness_center_google_event_ids')
	google_event_id = models.CharField(max_length=1024, blank=True)


class Vacation(Timeslot):
	"""
	Vacation can't be repeating
	"""

	healer = models.ForeignKey(Healer)

	@property
	def end(self):
		return datetime.combine(self.end_date, time()) + timedelta(minutes=self.end_time)

	def as_dict(self):
		slot = {'start_date': self.start_date.isoformat(),
				'start_time': self.start_time,
				'end_date': self.end_date.isoformat(),
				'end_time': self.end_time,
				'slot_id': self.id,
				'timeoff': 1}
		return slot

	def set_dates(self, start_dt, end_dt):
		self.start_date, self.start_time = get_date_minutes(start_dt)
		self.end_date, self.end_time = get_date_minutes(end_dt)

	def get_dates(self):
		"""
		Returns vacation dates list
		"""
		dates = []
		if self.end_date==self.start_date:
			dates.append(self.start_date)
		else:
			delta = self.end_date - self.start_date
			for day in range(0, delta.days+1):
				dates.append(self.start_date + timedelta(days=day))
		return dates

	def split_by_date(self):
		"""
		Returns vacations list splitted by date
		"""
		vacations = []
		if self.end_date==self.start_date:
			vacations.append(self)
		else:
			delta = self.end_date - self.start_date
			for day in range(0, delta.days+1):
				new_date = self.start_date + timedelta(days=day)
				vac = Vacation(id=self.id, healer=self.healer, start_date=new_date, end_date=new_date)
				if day == 0:
					vac.start_time = self.start_time
					vac.end_time = 1440
				elif day == delta.days:
					vac.start_time = 0
					vac.end_time = self.end_time
				else:
					vac.start_time = 0
					vac.end_time = 1440
				vacations.append(vac)
		return vacations

	@classmethod
	def check_for_conflicts(cls, timeslot):
		"""
		Find conflicts timeslot with vacations
		"""
		qs = Vacation.objects.filter(healer=timeslot.healer).filter_by_datetime(timeslot.start)

		for vacation in qs:
			if timeslot.is_single():
				if not (timeslot.end<=vacation.start or timeslot.start>=vacation.end):
					return True
			else:
				vacation_dates = vacation.get_dates()
				for vacation_date in vacation_dates:
					if timeslot.is_rule_conflict(vacation_date, repeating=False):
						return True

		return False

	def __unicode__(self):
		return "Healer: %s Start: %s End: %s" % (self.healer, self.start, self.end)


class UnavailableSlot(Timeslot):
	"""
	Unavailable slot from external calendar
	"""
	healer = models.ForeignKey(Healer)
	calendar = models.ForeignKey(UnavailableCalendar, blank=True, null=True)
	api = models.PositiveSmallIntegerField(choices=API_CHOICES)
	title = models.CharField(max_length=1024, blank=True)
	event_id = models.CharField(max_length=1024, blank=True)

	def __unicode__(self):
		return "Healer: %s Start: %s End: %s" % (self.healer, self.start, self.end)


class OnewayFriendshipManager(FriendshipManager):
	def refers_to(self, user1, user2):
		if self.filter(from_user=user1, to_user=user2).count() > 0:
			return True
		else:
			return False

	def referrals_to(self, user, count=False):
		if count:
			return self.filter(to_user=user).count()

		else:
			friends = []
			for friendship in self.filter(to_user=user).select_related():
				friends.append({"friend": friendship.from_user, "friendship": friendship})
			return friends

	def referrals_from(self, user, exclude_users=None, limit=None, random=False, count=False):
		if count:
			return self.filter(from_user=user).count()

		else:
			friendships = self.filter(from_user=user).select_related()
			if exclude_users:
				friendships = friendships.exclude(to_user__in=exclude_users)
			if random:
				friendships = friendships.order_by('?')
			if limit:
				friendships = friendships[:limit]
			friends = []
			for friendship in friendships:
				friends.append({"friend": friendship.to_user, "friendship": friendship})
			return friends

	def remove(self, user1, user2):
		referral = self.filter(from_user=user1, to_user=user2)

		try:
			referral[0].delete()
			return True
		except IndexError:
			return False

	def remove_bidirectional(self, user1, user2):
		if not self.remove(user1, user2):
			self.remove(user2, user1)


class Referrals(Friendship):
	objects = OnewayFriendshipManager()


class ReferralInvitation(FriendshipInvitation):
	objects = FriendshipInvitationManager()


class Clients(Friendship):
	objects = OnewayFriendshipManager()


class ClientInvitation(FriendshipInvitation):
	objects = FriendshipInvitationManager()


#def request_friendship(from_user, to_user, InvitationClass):
#	if to_user.has_usable_password() and from_user.has_usable_password():
#		invitation_to = InvitationClass.objects.filter(from_user=from_user, to_user=to_user, status="2")
#		invitation_from = InvitationClass.objects.filter(from_user=to_user, to_user=from_user, status="2")
#
#	add	if not invitation_from and not invitation_to:
#			invitation = InvitationClass(from_user=from_user, to_user=to_user, message="", status="2")
#			invitation.save()


def is_my_client(healer_user, client_user):
	return Clients.objects.refers_to(healer_user, client_user) or\
		   Referrals.objects.refers_to(healer_user, client_user)


def is_wcenters_client(healer_user, client_user):
	healer = Healer.objects.get(user=healer_user)
	wellness_centers = healer.get_wellness_centers()
	for wcenter in wellness_centers:
		if is_my_client(wcenter.user, client_user):
			return True


@receiver(post_save, sender=Location)
def location_changed_signal(instance, **kwargs):
	"""
	@type sender: Location
	@type instance: Location
	"""
	if instance.is_default:
		client_locations = instance.clientlocation_set.all()
		for client_location in client_locations:
			healer = Healer.objects.get(pk=client_location.client)
			healer.default_location = \
				instance.city_text() if instance.city_text() != '' \
					else instance.title
			healer.save()


def is_healer(client):
	if not client or not client.id:
		return None

	if not isinstance(client, Client):
		try:
			client = client.client
		except Client.DoesNotExist:
			return None
		except AttributeError:
			return None

	try:
		healer = client.healer
		return healer
	except Healer.DoesNotExist:
		return None


def is_wellness_center(client):
	healer = is_healer(client)
	if not healer:
		return False

	try:
		wellness_center = healer.wellnesscenter
		return wellness_center

	except WellnessCenter.DoesNotExist:
		pass

	return False


def is_concierge(client):
	healer = is_healer(client)
	if not healer:
		return False

	try:
		concierge = healer.concierge
		return concierge

	except Concierge.DoesNotExist:
		pass

	return False


def get_account_type(user):
	if is_wellness_center(user):
		return 'Center'
	elif is_healer(user):
		return 'Healer'
	else:
		return 'Client'


def check_wellness_center_provider_perm(wc_user, provider_username):
	wcenter = is_wellness_center(wc_user)
	if not wcenter:
		return None, None
	try:
		healer = Healer.objects.get(user__username__iexact=provider_username,
									wellness_center_permissions=wcenter)
	except Healer.DoesNotExist:
		return wcenter, None

	if not wcenter.get_locations():
		return wcenter, None
	if not wcenter.is_healer_in_wcenter(healer.user):
		return wcenter, None
	if healer not in healers.utils.get_providers(wcenter):
		return wcenter, None
	return wcenter, healer


def wcenter_get_provider(wc_user, provider_username):
	wcenter, healer = check_wellness_center_provider_perm(wc_user, provider_username)
	return healer


def is_wellness_center_location(location_id):
	return is_wellness_center(ClientLocation.objects.get(location=location_id).client)

