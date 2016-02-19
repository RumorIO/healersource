from bs4 import BeautifulSoup
import mock
import json
import urllib
from datetime import date
from calendar import *
from avatar.forms import PrimaryAvatarForm
from avatar.models import Avatar
from pinax.apps.account.models import EmailAddress
from clients.models import Client, ReferralsSent
from modality.models import Modality
from sync_hs.models import GOOGLE_API
from rest_framework.test import APIClient

from django import test
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.http import HttpRequest
from django.conf import settings
from django_dynamic_fixture import G
from util import get_email, count_emails

from healers.ajax import *
from healers.forms import (HealerForm, VacationForm, LocationForm,
	TreatmentTypeForm, TreatmentTypeLengthForm, RoomForm)
from healers.models import *
import healers.models

healers.models.send_sms = mock.Mock()


def to_timestamp(dt):
	"""Converts a datetime object to UTC timestamp"""

	return timegm(dt.utctimetuple()) * 1000


def create_test_time():
	return datetime.utcnow().replace(hour=13, minute=0, second=0, microsecond=0)

settings.GET_NOW = create_test_time


def load_message(response):
	return json.loads(response)['message']


def create_appointment(**kwargs):
	if not 'created_by' in kwargs:
		kwargs['created_by'] = kwargs['healer'].user
	kwargs['created_date'] = settings.GET_NOW()
	kwargs['last_modified_by'] = kwargs['created_by']
	kwargs['last_modified_date'] = settings.GET_NOW()
	return Appointment.objects.create(**kwargs)


def create_timeslot(healer, start, end, location=None):
	return HealerTimeslot.objects.create(healer=healer,
		start_date=start.date(),
		end_date=end.date(),
		start_time=get_minutes(start),
		end_time=get_minutes(end),
		location=location)

all_fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'oauth.json', 'locations.json', 'treatments.json']


class HealersTest(test.TestCase):
	fixtures = all_fixtures

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()
		settings.FAKE_DATE = create_test_time()
		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)

		self.test_client = Client.objects.get(pk=5)

		self.treatment_length = TreatmentTypeLength.objects.all()[0]

		healers.models.send_sms.reset_mock()

	def is_book_online_and_color_on_location_form(self, response):
		return ('<label for="id_book_online_0">Book online:</label>' in
			response.content and '<label for="id_color">Color:</label>' in
			response.content)

	def create_appt(self, start, repeat_period=None, confirmed=True, location=None, include_end_date=False):
		end = start + timedelta(hours=2)
		data = {'healer': self.test_healer,
			'client': self.test_client,
			'start_date': start.date(),
			'start_time': get_minutes(start),
			'end_time': get_minutes(end),
			'repeat_period': repeat_period,
			'location': location,
			'confirmed': confirmed,
			'treatment_length': self.treatment_length}
		if include_end_date:
			data['end_date'] = end.date()
		create_appointment(**data)

	def tearDown(self):
		settings.GET_NOW = create_test_time

	def initialize_ajax_request(self, healer):
		request = HttpRequest()
		request.user = healer.user
		return request


class HealersReferralsToMeViewTest(HealersTest):
	def setUp(self):
		super(HealersReferralsToMeViewTest, self).setUp()
		self.test_healer1 = Healer.objects.get(pk=3)
		self.test_healer2 = Healer.objects.get(pk=4)
		self.test_healer2.profileVisibility = Healer.VISIBLE_CLIENTS
		self.test_healer2.save()

		Referrals.objects.create(from_user=self.test_healer1.user, to_user=self.test_healer.user)
		Referrals.objects.create(from_user=self.test_healer2.user, to_user=self.test_healer.user)

	def test_auth_view(self):
		response = self.client.get(reverse('referrals_to_me', args=[self.test_healer.user.username]))

		referrals = response.context['referrals_to_me']
		self.assertEqual(len(referrals), 2)
		self.assertEqual(len([r for r in referrals if hasattr(r, 'private')]), 0)

	def test_not_auth_view(self):
		self.client.logout()
		response = self.client.get(reverse('referrals_to_me', args=[self.test_healer.user.username]))

		referrals = response.context['referrals_to_me']
		self.assertEqual(len(referrals), 2)
		self.assertEqual(len([r for r in referrals if hasattr(r, 'private')]), 1)


class TimeslotCheckConflictTest(HealersTest):
	def setUp(self):
		super(TimeslotCheckConflictTest, self).setUp()

		" set up timeslot1 12 - 3pm "
		self.start1 = create_test_time()  # 12:00
		self.end1 = self.start1 + timedelta(hours=3)  # 15:00

		self.timeslot = create_timeslot(self.test_healer, self.start1, self.end1)

	def test_conflict1(self):
		" test 1. timeslot1  12-3pm, timeslot2 1-2pm "
		start2 = self.start1 + timedelta(hours=1)
		end2 = self.end1 - timedelta(hours=1)

		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_conflict2(self):
		" test 2. timeslot1  12-3pm, timeslot2 11-2pm "
		start2 = self.start1 - timedelta(hours=1)
		end2 = self.end1 - timedelta(hours=1)

		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_conflict3(self):
		" test 3. timeslot1  12-3pm, timeslot2 1-4pm "
		start2 = self.start1 + timedelta(hours=1)
		end2 = self.end1 + timedelta(hours=1)

		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_conflict4(self):
		" test 4. timeslot1  12-3pm, timeslot2 11-4pm "
		start2 = self.start1 - timedelta(hours=1)
		end2 = self.end1 + timedelta(hours=1)

		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_conflict5(self):
		" test 5. timeslot1  12-3pm, timeslot2 12-3pm "
		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, self.start1, self.end1))

	def test_timeslot_before(self):
		" timeslot1  12-3pm, timeslot2 9-11am "
		start2 = self.start1 - timedelta(hours=3)
		end2 = self.start1 - timedelta(hours=1)

		self.assertFalse(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_timeslot_before_border(self):
		" timeslot1  12-3pm, timeslot2 9-12pm "
		start2 = self.start1 - timedelta(hours=3)
		end2 = self.start1

		self.assertFalse(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_timeslot_after(self):
		" timeslot1  12-3pm, timeslot2 4-7pm "
		start2 = self.end1 + timedelta(hours=1)
		end2 = self.end1 + timedelta(hours=4)

		self.assertFalse(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_timeslot_after_border(self):
		" timeslot1  12-3pm, timeslot2 3-7pm "
		start2 = self.end1
		end2 = self.end1 + timedelta(hours=4)

		self.assertFalse(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_timeslot_conflict_appointment(self):
		HealerTimeslot.objects.all().delete()
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start1.date(),
			end_date=self.end1.date(),
			start_time=get_minutes(self.start1),
			end_time=get_minutes(self.end1),
			treatment_length=self.treatment_length)

		self.test_conflict1()

	def test_timeslot_conflict_vacation(self):
		HealerTimeslot.objects.all().delete()
		Vacation.objects.create(healer=self.test_healer,
			start_date=self.start1.date(),
			end_date=self.end1.date(),
			start_time=get_minutes(self.start1),
			end_time=get_minutes(self.end1))

		self.test_conflict1()

	def test_timeslot_rule_conflict(self):
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.end_date = None
		self.timeslot.save()

		start2 = self.start1 + timedelta(days=7, hours=1)
		end2 = self.end1 + timedelta(days=7)

		self.assertTrue(Timeslot.check_for_conflicts(self.test_healer, start2, end2))

	def test_timeslot_exception_no_conflict(self):
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.end_date = None
		self.timeslot.exceptions = [get_timestamp((self.start1 + timedelta(days=7)).date())]
		self.timeslot.save()

		start2 = self.start1 + timedelta(days=7, hours=1)
		end2 = self.end1 + timedelta(days=7)

		self.assertFalse(Timeslot.check_for_conflicts(self.test_healer, start2, end2))


class ProfileTest(HealersTest):
	def test_healers_view_correct_response(self):
		response = self.client.get(reverse('healer_list'))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(len(response.context['users']))

	def test_healers_view_search_correct_response(self):
		response = self.client.get(reverse('healer_list'), {'search': self.test_healer.user.username})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['users']), 0)


	def test_photo_edit_view_form(self):
		response = self.client.get(reverse('avatar_change'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['primary_avatar_form']), PrimaryAvatarForm)


	def test_healer_edit_view_form(self):
		response = self.client.get(reverse('healer_edit'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), HealerForm)

	def test_healer_edit_view_post(self):
		data = {'first_name': 'first name', 'last_name': 'last name',
				'about': '<div style="color: red;">test</div>', 'profileVisibility': 2, 'timezone': Timezone.TIMEZONE_CHOICES[0][0],
				'client_screening': 2, 'profile_completeness_reminder_interval': 2,
				'ghp_notification_frequency': 'every time'} #,
		#				'beta_tester': True}
		response = self.client.post(reverse('healer_edit'), data)

		healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(healer.user.first_name, data['first_name'])
		self.assertEqual(healer.user.last_name, data['last_name'])
		self.assertEqual(healer.about, '<div style="">\n   test\n  </div>')
		self.assertEqual(healer.profileVisibility, 2)
		self.assertEqual(healer.beta_tester, True)
		self.assertEqual(healer.client_screening, 2)
		self.assertEqual(healer.profile_completeness_reminder_interval, 2)

	def test_healer_edit_about_view_post(self):
		data = {'first_name': 'first name', 'last_name': 'last name',
				'about': '<p>test</p>test', 'profileVisibility': 2, 'timezone': Timezone.TIMEZONE_CHOICES[0][0],
				'client_screening': 2, 'profile_completeness_reminder_interval': 2,
				'ghp_notification_frequency': 'every time'} #,
		#				'beta_tester': True}
		response = self.client.post(reverse('healer_edit'), data)

		healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(healer.about, '<p>\n   test\n  </p>\n  test')

	def test_healer_edit_empty_about_view_post(self):
		data = {'first_name': 'first name', 'last_name': 'last name',
				'about': '', 'profileVisibility': 2, 'timezone': Timezone.TIMEZONE_CHOICES[0][0],
				'client_screening': 2, 'profile_completeness_reminder_interval': 2,
				'ghp_notification_frequency': 'every time'} #,
		#				'beta_tester': True}
		response = self.client.post(reverse('healer_edit'), data)

		healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(healer.about, '')

	#saving bookAheadDays commented in view
	#self.assertEqual(healer.bookAheadDays, 30)

	def test_embed_view_invalid_username(self):
		response = self.client.get(reverse('embed', args=['test']))

		self.assertEqual(response.status_code, 404)

	def test_embed_view_correct_response(self):
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['healer'], self.test_healer)

	def test_embed_not_my_client(self):
		self.test_healer.profileVisibility = Healer.VISIBLE_CLIENTS
		self.test_healer.save()

		self.test_client.user.set_password('test')
		self.test_client.user.save()
		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 404)

	def test_embed_my_client(self):
		self.test_healer.profileVisibility = Healer.VISIBLE_CLIENTS
		self.test_healer.save()

		self.test_client.user.set_password('test')
		self.test_client.user.save()
		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)

		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)

	def test_healer_view_invalid_username(self):
		response = self.client.get(reverse('healer_public_profile', args=['test', 'test', 'test']))

		self.assertEqual(response.status_code, 404)

	def test_healer_view_correct_response(self):
		response = self.client.get(self.test_healer.healer_profile_url())

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['healer'], self.test_healer)

class ProfileChangeReminderIntervalViewTest(HealersTest):

	def test_wrong_interval(self):
		self.test_healer.profile_completeness_reminder_interval = 1
		self.test_healer.save()
		response = self.client.get(reverse('healer_change_profile_reminder_interval'), {'interval': 'x'})

		self.test_healer = Healer.objects.get(id=self.test_healer.id)
		self.assertEqual(self.test_healer.profile_completeness_reminder_interval, 1)

	def test_success(self):
		response = self.client.get(reverse('healer_change_profile_reminder_interval'), {'interval': 4})

		self.test_healer = Healer.objects.get(id=self.test_healer.id)
		self.assertEqual(self.test_healer.profile_completeness_reminder_interval, 4)

#class ICalTest(HealersTest):
#
##	def test_ical_view_invalid_username(self):
##		response = self.client.get(reverse('healer_ical', args=['test']))
##		empty response throws exception
##		self.assertEqual(response, None)
#
#	def test_ical_view_correct_response(self):
#		appointment = create_appointment(healer=self.test_healer,
#												 client=Client.objects.get(pk=3),
#												 start=datetime.utcnow(),
#												 end=datetime.utcnow() + timedelta(hours=1),
#												 location=None)
#
#		response = self.client.get(reverse('healer_ical', args=[self.test_healer.user.username]))
#		self.assertContains(response, 'VCALENDAR')
#		self.assertContains(response, 'VEVENT')


class ScheduleViewTest(HealersTest):
	def test_availability_view_correct_response(self):
		response = self.client.get(reverse('availability'))

		self.assertEqual(response.status_code, 200)

	def test_no_treatments_redirect(self):
		self.test_healer.healer_treatment_types.all().delete()
		response = self.client.get(reverse('availability'))

		self.assertEqual(response.status_code, 200)

	def test_ensure_schedule_is_unavailable_before_adding_treatment_type(self):
		self.test_healer.healer_treatment_types.all().delete()
		response = self.client.post(reverse('schedule'))
		self.assertIn('You must add at least one Treatment Type', response.content)


class LocationViewTest(HealersTest):
	def setUp(self):
		super(LocationViewTest, self).setUp()
		ClientLocation.objects.all().delete()

	def test_form(self):
		response = self.client.get(reverse('location'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['location_form']), LocationForm)
		# room form unavailable for healers
		self.assertIsNone(response.context['room_form'])

	def test_form_include_book_online_and_color(self):
		response = self.client.get(reverse('location'))
		self.assertTrue(
			self.is_book_online_and_color_on_location_form(response))

	def test_form_no_book_online_and_color_on_account_setup(self):
		response = self.client.get(
			reverse('provider_setup', kwargs={'step': 2}))
		self.assertFalse(
			self.is_book_online_and_color_on_location_form(response))

	def test_form_post_success(self):
		response = self.client.post(reverse('location'),
				{'title': 'test',
					'addressVisibility': Healer.VISIBLE_EVERYONE,
					'address_line1': 'test',
					'address_line2': 'test',
					'postal_code': 'test',
					'city': 'test',
					'state_province': 'test',
					'country': 'test',
					'color': LOCATION_COLOR_LIST[1],
					'name': 'test',  # room name
					'book_online': '1',
					})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(ClientLocation.objects.filter(client=self.test_healer).count(), 1)
		location = Location.objects.filter(title='test')
		self.assertEqual(location.count(), 1)
		self.assertEqual(location[0].color, LOCATION_COLOR_LIST[1])

	def test_room_add_form_not_users_location(self):
		response = self.client.post(reverse('room_add', args = [1]), # location_id
			{'name': 'test'})
		self.assertEqual(response.status_code, 404)

	def create_client_location_and_room(self):
		location = Location.objects.get(id=1)
		ClientLocation(client=self.test_healer, location=location).save()
		response = self.client.post(reverse('room_add', args=[location.id]),
			{'name': 'test'})
		room_id = location.rooms.all()[0].pk
		return location, room_id, response

	def test_room_form(self):
		location, _, response = self.create_client_location_and_room()
		self.assertEqual(response.status_code, 302)
		rooms = location.rooms.all()
		self.assertEqual(rooms.count(), 1)
		self.assertEqual(rooms[0].name, 'test')

	def test_room_duplication(self):
		location, _, _ = self.create_client_location_and_room()
		self.client.post(reverse('room_add', args=[location.id]),
			{'name': 'test'})
		self.assertEqual(location.rooms.all().count(), 1)

	def test_room_edit(self):
		location, room_id, _ = self.create_client_location_and_room()
		response = self.client.post(reverse('room_edit', args=[room_id]),
			{'name': 'test_new'})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(location.rooms.all()[0].name, 'test_new')

	def test_room_edit_not_users_location(self):
		location, room_id, _ = self.create_client_location_and_room()
		ClientLocation.objects.all().delete()
		response = self.client.post(reverse('room_edit', args=[room_id]))
		self.assertEqual(response.status_code, 404)

	def test_room_delete(self):
		location, room_id, _ = self.create_client_location_and_room()
		response = self.client.post(reverse('room_delete', args=[room_id]))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(location.rooms.all().count(), 1)
		# delete room only if more than one room exist
		self.client.post(reverse('room_add', args=[location.id]),
			{'name': 'test2'})
		room_id = location.rooms.all()[1].pk
		self.client.post(reverse('room_delete', args=[room_id]))
		self.assertEqual(location.rooms.all().count(), 1)

	def test_room_delete_not_users_location(self):
		location, room_id, _ = self.create_client_location_and_room()
		ClientLocation.objects.all().delete()
		response = self.client.post(reverse('room_delete', args=[room_id]))
		self.assertEqual(response.status_code, 404)

	def test_schedule_not_visible_form_post_success(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_DISABLED
		self.test_healer.save()
		response = self.client.post(reverse('location'),
				{'title': 'test',
				 'addressVisibility': Healer.VISIBLE_EVERYONE,
				 'address_line1': 'test',
				 'address_line2': 'test',
				 'postal_code': 'test',
				 'city': 'test',
				 'state_province': 'test',
				 'country': 'test',
				 'name': 'test', # room name
				 'book_online': '1'
				 })

		self.assertEqual(response.status_code, 302)
		self.assertEqual(ClientLocation.objects.filter(client=self.test_healer).count(), 1)
		location = Location.objects.filter(title='test')
		self.assertEqual(location.count(), 1)
		self.assertEqual(location[0].color, LOCATION_COLOR_LIST[0])


class LocationEditViewTest(HealersTest):
	def setUp(self):
		super(LocationEditViewTest, self).setUp()
		ClientLocation.objects.all().delete()

	def test_no_access_404(self):
		response = self.client.get(reverse('location_edit', args=[1]))

		self.assertEqual(response.status_code, 404)

	def test_form(self):
		ClientLocation.objects.create(client=self.test_healer, location=Location.objects.get(pk=1))
		response = self.client.get(reverse('location_edit', args=[1]))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), LocationForm)

	def test_form_post_success(self):
		ClientLocation.objects.create(client=self.test_healer, location=Location.objects.get(pk=1))
		response = self.client.post(reverse('location_edit', args=[1]),
				{'title': 'test2',
					'addressVisibility': Healer.VISIBLE_EVERYONE,
					'address_line1': 'test2',
					'address_line2': 'test',
					'postal_code': 'test',
					'city': 'test',
					'state_province': 'test',
					'country': 'test',
					'color': LOCATION_COLOR_LIST[1],
					'book_online': '1'})
		self.assertEqual(ClientLocation.objects.filter(client=self.test_healer).count(), 1)
		location = Location.objects.filter(title='test2')
		self.assertEqual(location.count(), 1)
		self.assertEqual(location[0].color, LOCATION_COLOR_LIST[1])


class LocationDeleteViewTest(HealersTest):

	def setUp(self):
		super(LocationDeleteViewTest, self).setUp()
		ClientLocation.objects.all().delete()
		self.client_location = ClientLocation.objects.create(
			client=self.test_healer,
			location=Location.objects.create(title='test', is_default=True)
		)

	def test_no_access_404(self):
		self.client_location.client = Healer.objects.get(pk=3)
		self.client_location.save()
		response = self.client.get(
			reverse('location_delete', args=[self.client_location.location.id])
		)

		self.assertEqual(response.status_code, 404)

	def test_delete_last_redirect(self):
		response = self.client.get(
			reverse('location_delete', args=[self.client_location.location.id])
		)
		self.assertRedirects(response, reverse('location'), 302)
		client_location = ClientLocation.objects.get(id=self.client_location.id)
		self.assertFalse(client_location.location.is_deleted)

	def test_delete_success(self):
		client_location1 = ClientLocation.objects.create(
			client=self.test_healer,
			location=Location.objects.create(title='test1', is_default=False)
		)

		response = self.client.get(
			reverse('location_delete', args=[self.client_location.location.id])
		)

		self.assertRedirects(response, reverse('location'), 302)

		client_location = ClientLocation.objects.get(id=self.client_location.id)
		client_location1 = ClientLocation.objects.get(id=client_location1.id)
		self.assertTrue(client_location.location.is_deleted, True)
		self.assertEqual(client_location1.location.is_default, True)


class TreatmentViewTest(HealersTest):
	def test_form(self):
		response = self.client.get(reverse('treatment_types'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['treatment_form']), TreatmentTypeForm)
		self.assertEqual(type(response.context['treatment_length_form']), TreatmentTypeLengthForm)

	def test_form_post_success(self):
		treatment_type = TreatmentType.objects.get(id=self.treatment_length.treatment_type_id)
		self.assertEqual(treatment_type.is_default, True)

		data = {'title': 'test',
				'length_hour': 1,
				'length_minute': 30,
				'cost': '9.99',
				'description': 'test description'}
		response = self.client.post(reverse('treatment_types'), data)

		treatment_type = TreatmentType.objects.get(title='test')
		self.assertEqual(treatment_type.healer, self.test_healer)
		self.assertEqual(treatment_type.description, data['description'])
		self.assertEqual(treatment_type.is_default, False)

		treatment_length = TreatmentTypeLength.objects.get(treatment_type=treatment_type)
		self.assertEqual(treatment_length.length, 90)
		self.assertEqual(treatment_length.cost, data['cost'])
		self.assertEqual(treatment_length.is_default, True)

		treatment_type = TreatmentType.objects.get(id=self.treatment_length.treatment_type_id)
		self.assertEqual(treatment_type.is_default, True)

	def test_form_post_new_success(self):
		TreatmentType.objects.all().delete()

		data = {'title': 'test',
				'length_hour': 1,
				'length_minute': 30,
				'cost': '9.99',
				'description': 'test description'}
		response = self.client.post(reverse('treatment_types'), data)

		treatment_type = TreatmentType.objects.get(title='test')
		self.assertEqual(treatment_type.healer, self.test_healer)
		self.assertEqual(treatment_type.description, data['description'])
		self.assertEqual(treatment_type.is_default, True)

		treatment_length = TreatmentTypeLength.objects.get(treatment_type=treatment_type)
		self.assertEqual(treatment_length.length, 90)
		self.assertEqual(treatment_length.cost, data['cost'])
		self.assertEqual(treatment_length.is_default, True)


class TreatmentEditViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_type_edit', args=[self.treatment_type.id]))

		self.assertEqual(response.status_code, 404)

	def test_form(self):
		self.treatment_type = self.treatment_length.treatment_type
		response = self.client.get(reverse('treatment_type_edit', args=[self.treatment_type.id]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['treatment_form']), TreatmentTypeForm)
		self.assertEqual(type(response.context['treatment_length_form']), TreatmentTypeLengthForm)

	def test_form_post_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.assertEqual(self.treatment_type.is_default, True)

		data = {'title': 'test2',
				'length_hour': 1,
				'length_minute': 40,
				'cost': '19.99',
				'description': 'test2'}

		response = self.client.post(reverse('treatment_type_edit', args=[self.treatment_type.id]), data)

		self.assertRedirects(response, reverse('treatment_types'), 302)
		treatment_type = TreatmentType.objects.get(id=self.treatment_type.id)
		self.assertEqual(treatment_type.healer, self.test_healer)
		self.assertEqual(treatment_type.description, data['description'])
		self.assertEqual(treatment_type.is_default, True)

		treatment_length = TreatmentTypeLength.objects.get(treatment_type=treatment_type)
		self.assertEqual(treatment_length.length, self.treatment_length.length)
		self.assertEqual(treatment_length.cost, self.treatment_length.cost)

	def test_form_post_add_length_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.assertEqual(self.treatment_type.is_default, True)

		data = {'title': 'test2',
				'length_hour': 1,
				'length_minute': 40,
				'cost': '19.99',
				'description': 'test2',
				'add_length': 'value'}

		response = self.client.post(reverse('treatment_type_edit', args=[self.treatment_type.id]), data)

		self.assertRedirects(response, reverse('treatment_type_edit', args=[self.treatment_type.id]), 302)
		treatment_type = TreatmentType.objects.get(id=self.treatment_type.id)
		self.assertEqual(treatment_type.healer, self.test_healer)
		self.assertEqual(treatment_type.description, data['description'])
		self.assertEqual(treatment_type.is_default, True)

		self.assertEqual(treatment_type.lengths.count(), 2)
		treatment_length = TreatmentTypeLength.objects.get(treatment_type=treatment_type, length=100)
		self.assertEqual(treatment_length.cost, data['cost'])


class TreatmentDeleteViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_type_delete', args=[self.treatment_type.id]))

		self.assertEqual(response.status_code, 404)

	def test_delete_last_redirect(self):
		self.treatment_type = self.treatment_length.treatment_type
		response = self.client.get(reverse('treatment_type_delete', args=[self.treatment_type.id]))

		self.assertRedirects(response, reverse('treatment_types'), 302)
		self.assertEqual(TreatmentType.objects.count(), 1)

	def test_delete_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		treatment = TreatmentType.objects.create(healer=self.test_healer,
			title='test',
			is_default=False)

		response = self.client.post(reverse('treatment_type_delete', args=[self.treatment_type.id]))

		self.assertRedirects(response, reverse('treatment_types'), 302)

		self.assertEqual(TreatmentType.objects.get(id=self.treatment_type.id).is_deleted, True)
		self.assertEqual(TreatmentType.objects.get(id=treatment.id).is_default, True)


class TreatmentDefaultViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_type_default', args=[self.treatment_type.id]))

		self.assertEqual(response.status_code, 404)

	def test_set_default_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.assertEqual(self.treatment_type.is_default, True)

		treatment = TreatmentType.objects.create(healer=self.test_healer,
			title='test',
			is_default=False)

		response = self.client.post(reverse('treatment_type_default', args=[treatment.id]))

		self.assertRedirects(response, reverse('treatment_types'), 302)

		self.assertEqual(TreatmentType.objects.get(id=treatment.id).is_default, True)
		self.assertEqual(TreatmentType.objects.get(id=self.treatment_type.id).is_default, False)


class TreatmentLengthDeleteViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_length_delete', args=[self.treatment_length.id]))

		self.assertEqual(response.status_code, 404)

	def test_delete_last_redirect(self):
		self.treatment_type = self.treatment_length.treatment_type
		response = self.client.get(reverse('treatment_length_delete', args=[self.treatment_length.id]))

		self.assertRedirects(response, reverse('treatment_type_edit', args=[self.treatment_type.id]), 302)
		self.assertEqual(TreatmentTypeLength.objects.count(), 1)

	def test_delete_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		treatment_length = TreatmentTypeLength.objects.create(treatment_type=self.treatment_type,
			length=60,
			cost=10,
			is_default=False)

		response = self.client.post(reverse('treatment_length_delete', args=[self.treatment_length.id]))

		self.assertRedirects(response, reverse('treatment_type_edit', args=[self.treatment_type.id]), 302)

		self.assertEqual(TreatmentTypeLength.objects.get(id=self.treatment_length.id).is_deleted, True)
		self.assertEqual(TreatmentTypeLength.objects.get(id=treatment_length.id).is_default, True)


class TreatmentLengthDefaultViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_length_default', args=[self.treatment_length.id]))

		self.assertEqual(response.status_code, 404)

	def test_set_default_success(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.assertEqual(self.treatment_length.is_default, True)

		treatment_length = TreatmentTypeLength.objects.create(treatment_type=self.treatment_type,
			length=60,
			cost=10,
			is_default=False)

		response = self.client.post(reverse('treatment_length_default', args=[treatment_length.id]))

		self.assertRedirects(response, reverse('treatment_type_edit', args=[self.treatment_type.id]), 302)

		self.assertEqual(TreatmentTypeLength.objects.get(id=self.treatment_length.id).is_default, False)
		self.assertEqual(TreatmentTypeLength.objects.get(id=treatment_length.id).is_default, True)


class TreatmentLengthAddViewTest(HealersTest):
	def test_no_access_404(self):
		self.treatment_type = self.treatment_length.treatment_type
		self.treatment_type.healer = Healer.objects.get(pk=3)
		self.treatment_type.save()
		response = self.client.get(reverse('treatment_length_add', args=[self.treatment_length.id]))

		self.assertEqual(response.status_code, 404)

	def test_add_success(self):
		self.treatment_type = self.treatment_length.treatment_type

		data = {'length_hour': 1,
				'length_minute': 40,
				'cost': '19.99',
				}

		response = self.client.post(reverse('treatment_length_add', args=[self.treatment_type.id]), data)

		self.assertRedirects(response, reverse('treatment_types'))

		self.assertEqual(TreatmentTypeLength.objects.filter(treatment_type=self.treatment_type).count(), 2)


class HealerScheduleVisibilityTest(HealersTest):
	def setUp(self):
		super(HealerScheduleVisibilityTest, self).setUp()
		self.client.logout()
		self.test_client.user.set_password('test')
		self.test_client.user.save()

		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		self.schedule = '<div id="calendar"'

	def test_visible_everyone(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
		self.test_healer.save()

		self.client.logout()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertContains(response, self.schedule)

	#	def test_visible_registered(self):
	#		self.test_healer.scheduleVisibility = Healer.VISIBLE_REGISTERED
	#		self.test_healer.save()
	#
	#		response = self.client.get(reverse('healer_public_profile', args=[self.test_healer.user.username]))
	#		self.assertContains(response, self.schedule)
	#		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
	#		self.assertContains(response, self.schedule)
	#
	#		self.client.logout()
	#		response = self.client.get(reverse('healer_public_profile', args=[self.test_healer.user.username]))
	#		self.assertNotContains(response, self.schedule)
	#		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
	#		self.assertNotContains(response, self.schedule)

	def test_visible_client(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_CLIENTS
		self.test_healer.save()
		friendship = Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)

		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertContains(response, self.schedule)

		friendship.delete()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertNotContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertNotContains(response, self.schedule)

		self.client.logout()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertNotContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertNotContains(response, self.schedule)

	def test_visible_disabled(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_DISABLED
		self.test_healer.save()
		friendship = Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)

		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertNotContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertNotContains(response, self.schedule)

		friendship.delete()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertNotContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertNotContains(response, self.schedule)

		self.client.logout()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertNotContains(response, self.schedule)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertNotContains(response, self.schedule)

#	def test_no_treatments_disabled(self):
#		self.test_healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
#		self.test_healer.save()
#		self.test_healer.healer_treatment_types.all().delete()
#
#		self.client.logout()
#		response = self.client.get(reverse('healer_public_profile', args=[self.test_healer.user.username]))
#		self.assertNotContains(response, self.schedule)
#		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
#		self.assertNotContains(response, self.schedule)

class HealerProfileVisibilityTest(HealersTest):
	def setUp(self):
		super(HealerProfileVisibilityTest, self).setUp()
		self.client.logout()
		self.test_client.user.set_password('test')
		self.test_client.user.save()

		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		self.test_healer.about = "--test string--"
		self.test_healer.save()

		self.schedule = '<div id="calendar"'

	def test_visible_everyone(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
		self.test_healer.profileVisibility = Healer.VISIBLE_EVERYONE
		self.test_healer.save()

		self.client.logout()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertContains(response, self.test_healer.about)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertContains(response, self.schedule)

	#	def test_visible_registered(self):
	#		self.test_healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
	#		self.test_healer.profileVisibility = Healer.VISIBLE_REGISTERED
	#		self.test_healer.save()
	#
	#		response = self.client.get(reverse('healer_public_profile', args=[self.test_healer.user.username]))
	#		self.assertContains(response, self.test_healer.about)
	#		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
	#		self.assertContains(response, self.schedule)
	#
	#		self.client.logout()
	#		response = self.client.get(reverse('healer_public_profile', args=[self.test_healer.user.username]))
	#		self.assertEqual(response.status_code, 404)
	#		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
	#		self.assertEqual(response.status_code, 404)

	def test_visible_client(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
		self.test_healer.profileVisibility = Healer.VISIBLE_CLIENTS
		self.test_healer.save()
		friendship = Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)

		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertContains(response, self.test_healer.about)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertContains(response, self.schedule)

		friendship.delete()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertEqual(response.status_code, 404)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertEqual(response.status_code, 404)

		self.client.logout()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertEqual(response.status_code, 404)
		response = self.client.get(reverse('embed', args=[self.test_healer.user.username]))
		self.assertEqual(response.status_code, 404)


class HealerReviewLinkVisibilityTest(HealersTest):
	"""
	#259 - the 'x reviews' link should follow review_permission rules
	"""

	def test_visible(self):
		for permission in (Healer.VISIBLE_CLIENTS, Healer.VISIBLE_EVERYONE):
			self.test_healer.review_permission = permission
			self.test_healer.save()
			response = self.client.get(self.test_healer.healer_profile_url())
			self.assertTrue('reviews_link' in response.content)

	def test_hidden(self):
		self.test_healer.review_permission = Healer.VISIBLE_DISABLED
		self.test_healer.save()
		response = self.client.get(self.test_healer.healer_profile_url())
		self.assertFalse('reviews_link' in response.content)


class HealerConfirmationAutoTest(HealersTest):
	" Test automatically confirm all appointments "

	def setUp(self):
		super(HealerConfirmationAutoTest, self).setUp()
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
		self.test_healer.save()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=1)

	def test_client_user(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]
		self.assertTrue(appointment.confirmed)

	def test_new_user(self):
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)

		appointment = results[0]
		self.assertTrue(appointment.confirmed)

	def test_dummy_user(self):
		self.test_client.user.is_active = False
		self.test_client.user.set_unusable_password()
		self.test_client.user.save()
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertTrue(appointment.confirmed)


class HealerConfirmationManualNewTest(HealersTest):
	" Test manually confirm appointments for new clients only "

	def setUp(self):
		super(HealerConfirmationManualNewTest, self).setUp()
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL_NEW
		self.test_healer.save()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=1)

	def test_client_user(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertTrue(appointment.confirmed)

	def test_client_user_other_order(self):
		Clients.objects.create(from_user=self.test_client.user, to_user=self.test_healer.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertFalse(appointment.confirmed)

	def test_refferal_user(self):
		Referrals.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertTrue(appointment.confirmed)

	def test_refferal_user_other_order(self):
		Referrals.objects.create(from_user=self.test_client.user, to_user=self.test_healer.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertFalse(appointment.confirmed)

	def test_new_user(self):
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertFalse(appointment.confirmed)


class HealerConfirmationManualTest(HealersTest):
	" Test manually confirm appointments for new clients only "

	def setUp(self):
		super(HealerConfirmationManualTest, self).setUp()
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL
		self.test_healer.save()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=1)

	def test_client_user(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertFalse(appointment.confirmed)

	def test_new_user(self):
		results = Appointment.create_new(healer_user_id=self.test_healer.user.id,
			client_id=self.test_client.id,
			start=self.start,
			end=self.end,
			location_id=None,
			room_id=None,
			creator_user=self.test_client.user,
			treatment_length=self.treatment_length,
			creator=self.test_client.user)
		appointment = results[0]

		self.assertFalse(appointment.confirmed)


class AppointmentsConfirmTest(HealersTest):
	def setUp(self):
		super(AppointmentsConfirmTest, self).setUp()
		start = create_test_time() + timedelta(hours=2)
		end = start + timedelta(hours=2)
		location = Location.objects.get(pk=1)
		client1 = Client.objects.get(pk=3)
		client1.approval_rating = 0
		client1.save()

		client2 = Client.objects.get(pk=5)

		self.appointment1 = create_appointment(healer=self.test_healer,
			client=client1,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=location,
			confirmed=False,
			treatment_length=self.treatment_length,
			created_by=client1.user)

		self.appointment2 = create_appointment(healer=self.test_healer,
			client=client2,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=location,
			confirmed=False,
			treatment_length=self.treatment_length,
			created_by=client1.user)


class AppointmentsViewTest(HealersTest):
	def test_correct_response(self):
		response = self.client.get(reverse('appointments'))

		self.assertEqual(response.status_code, 200)

	def test_no_treatments(self):
		self.test_healer.healer_treatment_types.all().delete()
		response = self.client.get(reverse('appointments'))

		self.assertEqual(response.status_code, 200)


class AppointmentsHistoryViewTest(HealersTest):
	def test_get(self):
		#repeat 3 times
		self.create_appt(
			create_test_time() - timedelta(weeks=2),
			repeat_period=rrule.WEEKLY)

		#single
		self.create_appt(create_test_time() - timedelta(weeks=3))

		#single unconfirmed
		self.create_appt(
			create_test_time() - timedelta(weeks=3),
			confirmed=False)

		#single out bottom border
		self.create_appt(create_test_time() - timedelta(days=730))

		#single out top border
		self.create_appt(create_test_time() + timedelta(weeks=1))

		response = self.client.get(reverse('appointment_history'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['appointment_list']), 4)


class ConfirmedAppointmentsViewTest(HealersTest):
	def setUp(self):
		super(ConfirmedAppointmentsViewTest, self).setUp()
		start = create_test_time()
		end = start + timedelta(hours=2)
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			location=None,
			confirmed=True,
			treatment_length=self.treatment_length)

	def test_current_month_correct_response(self):
		response = self.client.get(reverse('current_confirmed_appointments'))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(len(response.context['appointments']) >= 1)
		self.assertTrue(len(response.context['appointments']) <= 5)

	def test_next_month_correct_response(self):
		next_month = create_test_time().date()
		if next_month.month == 12:
			next_month = next_month.replace(year=next_month.year + 1, month=1, day=1)
		else:
			next_month = next_month.replace(month=next_month.month + 1, day=1)
		response = self.client.get(reverse('confirmed_appointments',
			args=[next_month.strftime('%Y'), next_month.strftime('%m')]))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(len(response.context['appointments']) in [4, 5])

	def test_prev_month_404(self):
		prev_month = create_test_time().date()
		if prev_month.month == 1:
			prev_month = prev_month.replace(year=prev_month.year - 1, month=12, day=1)
		else:
			prev_month = prev_month.replace(month=prev_month.month - 1, day=1)
		response = self.client.get(reverse('confirmed_appointments',
			args=[prev_month.strftime('%Y'), prev_month.strftime('%m')]))

		self.assertEqual(response.status_code, 404)


class AppointmentConfirmViewTest(AppointmentsConfirmTest):
	def test_wrong_appointment_fail(self):
		response = self.client.get(reverse('appointment_confirm', args=[0]))

		self.assertEqual(response.status_code, 404)

	def test_appointment_conflict(self):
		self.appointment2.confirmed = True
		self.appointment2.save()
		response = self.client.get(reverse('appointment_confirm', args=[self.appointment1.id]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertFalse(Appointment.objects.filter(pk=self.appointment1.pk).count())
		email = get_email()
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(response.content.find('conflict'), -1)

	def test_vacation_warning(self):
		vacation = Vacation.objects.create(healer=self.test_healer,
			start_date=self.appointment1.start_date,
			end_date=self.appointment1.end_date,
			start_time=self.appointment1.start_time,
			end_time=self.appointment1.end_time)
		response = self.client.get(reverse('appointment_confirm', args=[self.appointment1.id]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertTrue(Appointment.objects.get(pk=self.appointment1.pk).confirmed)

		self.assertTrue(Vacation.objects.filter(pk=vacation.pk).count())
		self.assertNotEqual(response.content.find('take care'), -1)

	def test_correct_response(self):
		response = self.client.get(reverse('appointment_confirm', args=[self.appointment1.id]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertNotEqual(response.content.find('confirmed'), -1)
		self.assertTrue(Appointment.objects.get(pk=self.appointment1.pk).confirmed)
		self.assertEqual(Appointment.objects.get(pk=self.appointment1.pk).last_modified_by, self.test_healer.user)
		self.assertFalse(Appointment.objects.filter(pk=self.appointment2.pk).count())
		self.assertEqual(Appointment.all_objects.get(pk=self.appointment1.pk).last_modified_by, self.test_healer.user)

		self.assertEqual(Client.objects.get(pk=self.appointment1.client.pk).approval_rating, 100)

		email = get_email()
		self.assertNotEqual(email.subject.find('confirmed'), -1)
		self.assertNotEqual(email.body.find(self.appointment1.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)
		email = get_email(1)
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertEqual(email.to[0], self.appointment2.client.user.email)


class AppointmentConfirmAllViewTest(AppointmentsConfirmTest):
	def test_appointment_conflict(self):
		self.appointment2.confirmed = True
		self.appointment2.save()
		response = self.client.get(reverse('appointment_confirm_all', args=[self.test_healer.user.username]),
			follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertFalse(Appointment.objects.filter(pk=self.appointment1.pk).count())
		email = get_email()
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(response.content.find('conflict'), -1)

	def test_vacation_warning(self):
		vacation = Vacation.objects.create(healer=self.test_healer,
			start_date=self.appointment1.start_date,
			end_date=self.appointment1.end_date,
			start_time=self.appointment1.start_time,
			end_time=self.appointment1.end_time)
		response = self.client.get(reverse('appointment_confirm_all', args=[self.test_healer.user.username]),
			follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertTrue(Appointment.objects.get(pk=self.appointment1.pk).confirmed)

		self.assertTrue(Vacation.objects.filter(pk=vacation.pk).count())
		self.assertNotEqual(response.content.find('take care'), -1)

	def test_correct_response(self):
		self.appointment2.start_time += 120
		self.appointment2.end_time += 120
		self.appointment2.save()

		response = self.client.get(reverse('appointment_confirm_all', args=[self.test_healer.user.username]),
			follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertNotEqual(response.content.find('confirmed'), -1)
		self.assertTrue(Appointment.objects.get(pk=self.appointment1.pk).confirmed)
		self.assertTrue(Appointment.objects.get(pk=self.appointment2.pk).confirmed)

		self.assertEqual(Client.objects.get(pk=self.appointment1.client.pk).approval_rating, 100)

		self.assertEqual(Client.objects.get(pk=self.appointment2.client.pk).approval_rating, 100)

		email = get_email()
		self.assertNotEqual(email.subject.find('confirmed'), -1)
		self.assertNotEqual(email.body.find(self.appointment1.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)
		email = get_email(1)
		self.assertNotEqual(email.subject.find('confirmed'), -1)
		self.assertNotEqual(email.body.find(self.appointment2.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment2.client.user.email)


class AppointmentDeclineViewTest(AppointmentsConfirmTest):
	def test_wrong_appointment_fail(self):
		response = self.client.get(reverse('appointment_decline', args=[0]))

		self.assertEqual(response.status_code, 404)

	def test_correct_response(self):
		response = self.client.get(reverse('appointment_decline', args=[self.appointment1.id]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertEqual(Appointment.objects.filter(pk=self.appointment1.pk).count(), 0)
		self.assertEqual(Appointment.canceled_objects.get(pk=self.appointment1.pk).last_modified_by, self.test_healer.user)
		self.assertNotEqual(response.content.find('declined'), -1)

		email = get_email()
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertNotEqual(email.body.find(self.appointment1.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)

	def test_decline_confirmed_correct_response(self):
		self.appointment1.confirmed = True
		self.appointment1.save()
		response = self.client.get(reverse('appointment_decline', args=[self.appointment1.id]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertEqual(Appointment.objects.filter(pk=self.appointment1.pk).count(), 0)
		self.assertNotEqual(response.content.find('canceled'), -1)

		email = get_email()
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertNotEqual(email.body.find(self.appointment1.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)


class AppointmentDeclineAllViewTest(AppointmentsConfirmTest):
	def test_correct_response(self):
		response = self.client.get(reverse('appointment_decline_all', args=[self.test_healer.user.username]), follow=True)

		self.assertRedirects(response, reverse('appointments', args=[self.test_healer.user.username]), 302)
		self.assertEqual(Appointment.objects.all().count(), 0)
		self.assertNotEqual(response.content.find('declined'), -1)

		email = get_email()
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertNotEqual(email.body.find(self.appointment1.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment1.client.user.email)
		email = get_email(1)
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertNotEqual(email.body.find(self.appointment2.date_range_text()), -1)
		self.assertEqual(email.to[0], self.appointment2.client.user.email)


class VacationTest(HealersTest):
	def test_vacation_view_form(self):
		response = self.client.get(reverse('vacation'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), VacationForm)

	def test_vacation_view_form_post_end_lt_start(self):
		start = create_test_time()
		end = start - timedelta(hours=2)

		response = self.client.post(reverse('vacation'),
				{'start_0': start.strftime('%m/%d/%Y'),
				 'start_1': start.strftime('%I:%M%p'),
				 'end_0': end.strftime('%m/%d/%Y'),
				 'end_1': end.strftime('%I:%M%p')})

		self.assertEqual(response.status_code, 200)

		self.assertTrue(len(response.context['form'].errors))


	def test_vacation_view_form_post_invalid_dates(self):
		response = self.client.post(reverse('vacation'),
				{'start_0': 'test',
				 'start_1': 'test',
				 'end_0': 'test',
				 'end_1': 'test'})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(len(response.context['form'].errors))

	def test_vacation_view_form_post(self):
		start = create_test_time()
		end = start + timedelta(days=1)

		response = self.client.post(reverse('vacation'),
				{'start_0': start.strftime('%m/%d/%Y'),
				 'start_1': start.strftime('%I:%M%p'),
				 'end_0': end.strftime('%m/%d/%Y'),
				 'end_1': end.strftime('%I:%M%p')})

		self.assertEqual(response.status_code, 200)

		vacation_count = Vacation.objects.filter(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date()).count()
		self.assertEqual(vacation_count, 1)

	def test_vacation_delete_view_not_found(self):
		response = self.client.get(reverse('vacation_delete', args=[0]))

		self.assertEqual(response.status_code, 404)

	def test_vacation_delete_view_no_access(self):
		start = create_test_time()
		end = create_test_time() + timedelta(hours=2)
		vacation = Vacation.objects.create(healer=Healer.objects.get(pk=3),
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		response = self.client.get(reverse('vacation_delete', args=[vacation.id]))

		self.assertContains(response, 'Not Allowed', status_code=404)

	def test_vacation_delete_view_correct_response(self):
		start = create_test_time()
		end = create_test_time() + timedelta(hours=2)
		vacation = Vacation.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		response = self.client.get(reverse('vacation_delete', args=[vacation.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Vacation.objects.filter(pk=vacation.pk).count(), 0)


class FriendsTest(HealersTest):
	def test_friends_view_refferals_correct_response(self):
		response = self.client.get(reverse('friends', args=['referrals']))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['friend_type'], 'referrals')

	def test_friends_view_clients_correct_response(self):
		response = self.client.get(reverse('friends', args=['clients']))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['friend_type'], 'clients')


#class FriendsSearchViewTest(HealersTest):
#	def test_refferals_empty_message(self):
#		response = self.client.get(reverse('friends_search', args=['referrals']))
#
#		self.assertEqual(response.status_code, 200)
#		self.assertContains(response, "match any results")
#
#	def test_refferals_no_healer_message(self):
#		# ceil is client only
#		response = self.client.get(reverse('friends_search', args=['referrals']), {'query': 'ceil'}, follow=True)
#
#		self.assertEqual(response.status_code, 200)
#		self.assertContains(response, "match any results")
#
#	def test_refferals_firstname_success(self):
#		response = self.client.get(reverse('friends_search', args=['referrals']), {'query': 'ken'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_refferals_lastname_success(self):
#		response = self.client.get(reverse('friends_search', args=['referrals']), {'query': 'rich'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_refferals_email_success(self):
#		response = self.client.get(reverse('friends_search', args=['referrals']), {'query': 'ken@healersource.com'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_email_exact_success(self):
#		u = User.objects.get(email='ken@healersource.com')
#		u.first_name = 'ken@healersource'
#		u.save()
#		response = self.client.get(reverse('friends_search', args=['referrals']), {'query': 'ken@healersource'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 0)
#
#	def test_clients_empty_message(self):
#		response = self.client.get(reverse('friends_search', args=['clients']))
#
#		self.assertEqual(response.status_code, 200)
#		self.assertContains(response, "match any results")
#
#	def test_clients_no_results_message(self):
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'abc'}, follow=True)
#
#		self.assertEqual(response.status_code, 200)
#		self.assertContains(response, "match any results")
#
#	def test_clients_firstname_success(self):
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'ceil'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_clients_lastname_success(self):
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'michelle'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_clients_email_success(self):
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'ceil@healersource.com'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 1)
#
#	def test_clients_skip_unregistered_success(self):
#		User.objects.filter(email='ceil@healersource.com').update(is_active=False)
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'ceil@healersource.com'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertContains(response, "match any results")
#
#	def test_clients_skip_unapproved_success(self):
#		client = Client.objects.get(user__email='ceil@healersource.com')
#		client.approval_rating = 0
#		client.save()
#		response = self.client.get(reverse('friends_search', args=['clients']), {'query': 'ceil@healersource.com'})
#
#		self.assertEqual(response.status_code, 200)
#		self.assertEqual(len(response.context['found_clients']), 0)
#		self.assertContains(response, "match any results")

class ReferClientTest(HealersTest):
	def setUp(self):
		super(ReferClientTest, self).setUp()
		self.ref_client = Client.objects.get(pk=3)
		self.healer = Healer.objects.get(pk=4)
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.ref_client.user)
		Referrals.objects.create(from_user=self.test_healer.user, to_user=self.healer.user)

	# def test_clients_list(self):
	# 	response = self.client.get(reverse('refer_clients_list', args=[self.healer.user.username]))
	# 	self.assertEqual(response.status_code, 200)
	#
	# 	self.assertEqual(len(response.context['friends']), 2)
	# 	self.assertEqual(response.context['friends'][0], self.ref_client.user)
	#
	# def test_providers_list(self):
	# 	response = self.client.get(reverse('refer_providers_list', args=[self.ref_client.user.username]))
	# 	self.assertEqual(response.status_code, 200)
	#
	# 	self.assertEqual(len(response.context['friends']), 1)
	# 	self.assertEqual(response.context['friends'][0], self.healer.user)

	def test_refer_from_providers(self):
		response = self.client.get(reverse('refer_from_providers', args=[self.healer.user.username, self.ref_client.user.username]))
		self.assertEqual(response.status_code, 200)

		self.assertEqual(Clients.objects.filter(from_user=self.healer.user, to_user=self.ref_client.user).count(), 1)
		self.assertEqual(ReferralsSent.objects.filter(
			provider_user=self.healer.user,
			client_user=self.ref_client.user,
			referring_user=self.test_healer.user).count(), 1)

		email = get_email(0)
		self.assertEqual(email.to, [self.healer.user.email])
		self.assertTrue("has Referred a New Client to you" in email.subject)
		self.assertTrue(str(self.ref_client) in email.body)

	def test_refer_from_clients(self):
		response = self.client.get(reverse('refer_from_clients', args=[self.healer.user.username, self.ref_client.user.username]))
		self.assertEqual(response.status_code, 200)

		self.assertEqual(Clients.objects.filter(from_user=self.healer.user, to_user=self.ref_client.user).count(), 1)
		self.assertEqual(ReferralsSent.objects.filter(
			provider_user=self.healer.user,
			client_user=self.ref_client.user,
			referring_user=self.test_healer.user).count(), 1)

		email = get_email(0)
		self.assertEqual(email.to, [self.ref_client.user.email])
		self.assertTrue("has referred" in email.subject)
		self.assertTrue(str(self.healer.user.client) in email.body)

	def test_client_exists(self):
		Clients.objects.create(from_user=self.healer.user, to_user=self.ref_client.user)

		response = self.client.get(reverse('refer_from_clients', args=[self.healer.user.username, self.ref_client.user.username]))
		self.assertEqual(response.status_code, 200)

		self.assertEqual(ReferralsSent.objects.filter(
			provider_user=self.healer.user,
			client_user=self.ref_client.user,
			referring_user=self.test_healer.user).count(), 0)

		self.assertFalse(count_emails())

	def test_referralssent_exists(self):
		ReferralsSent.objects.create(
			provider_user=self.healer.user,
			client_user=self.ref_client.user,
			referring_user=self.test_healer.user)

		response = self.client.get(reverse('refer_from_clients', args=[self.healer.user.username, self.ref_client.user.username]))
		self.assertEqual(response.status_code, 200)

		self.assertEqual(ReferralsSent.objects.filter(
			provider_user=self.healer.user,
			client_user=self.ref_client.user,
			referring_user=self.test_healer.user).count(), 1)

		self.assertFalse(count_emails())

	def test_appointments_number(self):
		now = create_test_time().date()
		G(Appointment,
		  healer=self.healer,
			repeat_period=None,
			start_date=now-timedelta(days=1),
			end_date=now-timedelta(days=1),
			client=self.ref_client) # 1 single

		G(Appointment,
		  healer=self.healer,
			repeat_period=rrule.DAILY,
			repeat_count=3,
			start_date=now-timedelta(days=5),
			end_date=now-timedelta(days=2),
			client=self.ref_client) # 3 daily

		G(Appointment,
		  healer=self.healer,
			repeat_period=rrule.WEEKLY,
			repeat_count=3,
			start_date=now-timedelta(weeks=2),
			end_date=now+timedelta(weeks=1),
			client=self.ref_client) # 2 weekly

		G(Appointment,
		  healer=self.healer,
			repeat_period=rrule.WEEKLY,
			repeat_count=None,
			start_date=now-timedelta(weeks=2),
			end_date=None,
			client=self.ref_client) # 2 weekly ongoing


		appts_count = Appointment.objects.estimate_number([self.ref_client.user], self.healer)
		self.assertEqual(appts_count[self.ref_client.user], 8)

class FriendProcessTest(HealersTest):
	def setUp(self):
		super(FriendProcessTest, self).setUp()
		self.friend = Client.objects.get(pk=3)
		self.test_healer2 = Healer.objects.get(pk=4)

	def test_friend_process_view_invite(self):
		response = self.client.get(reverse('friend_invite', args=['clients', self.friend.user.id]))
		self.assertEqual(response.status_code, 302)

		invitations = ClientInvitation.objects.filter(from_user=self.test_healer.user, to_user=self.friend.user)
		self.assertEqual(invitations.count(), 1)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('has Requested'), -1)

	def test_friend_process_view_invite_screen_none(self):
		self.test_healer2.client_screening = Healer.SCREEN_NONE
		self.test_healer2.save()

		response = self.client.get(reverse('friend_invite', args=['clients', self.test_healer2.user.id]))
		self.assertEqual(response.status_code, 302)

		invitations = ClientInvitation.objects.filter(to_user=self.test_healer2.user, from_user=self.test_healer.user)
		self.assertEqual(invitations.count(), 0)

		clients = Clients.objects.filter(to_user=self.test_healer.user, from_user=self.test_healer2.user)
		self.assertEqual(clients.count(), 1)

		self.assertEqual(count_emails(), 0)

	def test_friend_process_view_invite_screen_not_contacts_contact(self):
		self.test_healer2.client_screening = Healer.SCREEN_NOT_CONTACTS
		self.test_healer2.save()

		ContactEmail.objects.create(email=self.test_healer.user.email, contact=ContactInfo.objects.create(healer=self.test_healer2))

		response = self.client.get(reverse('friend_invite', args=['clients', self.test_healer2.user.id]))
		self.assertEqual(response.status_code, 302)

		invitations = ClientInvitation.objects.filter(to_user=self.test_healer2.user, from_user=self.test_healer.user)
		self.assertEqual(invitations.count(), 0)

		clients = Clients.objects.filter(to_user=self.test_healer.user, from_user=self.test_healer2.user)
		self.assertEqual(clients.count(), 1)

		self.assertEqual(count_emails(), 0)

	def test_friend_process_view_invite_screen_not_contacts(self):
		self.test_healer2.client_screening = Healer.SCREEN_NOT_CONTACTS
		self.test_healer2.save()

		response = self.client.get(reverse('friend_invite', args=['clients', self.test_healer2.user.id]))
		self.assertEqual(response.status_code, 302)

		invitations = ClientInvitation.objects.filter(to_user=self.test_healer2.user, from_user=self.test_healer.user)
		self.assertEqual(invitations.count(), 1)

		clients = Clients.objects.filter(to_user=self.test_healer.user, from_user=self.test_healer2.user)
		self.assertEqual(clients.count(), 0)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('has Requested'), -1)

	def test_friend_process_view_invite_screen_all(self):
		self.test_healer2.client_screening = Healer.SCREEN_ALL
		self.test_healer2.save()

		ContactEmail.objects.create(email=self.test_healer.user.email, contact=ContactInfo.objects.create(healer=self.test_healer2))

		response = self.client.get(reverse('friend_invite', args=['clients', self.test_healer2.user.id]))
		self.assertEqual(response.status_code, 302)

		invitations = ClientInvitation.objects.filter(to_user=self.test_healer2.user, from_user=self.test_healer.user)
		self.assertEqual(invitations.count(), 1)

		clients = Clients.objects.filter(to_user=self.test_healer.user, from_user=self.test_healer2.user)
		self.assertEqual(clients.count(), 0)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('has Requested'), -1)

	def test_friend_process_view_accept(self):
		invitation1 = ReferralInvitation.objects.create(from_user=self.friend.user,
			to_user=self.test_healer.user,
			message="",
			status="2")
		invitation2 = ReferralInvitation.objects.create(from_user=self.friend.user,
			to_user=self.test_healer.user,
			message="",
			status="2")

		response = self.client.get(reverse('friend_accept', args=['referrals', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(ReferralInvitation.objects.get(pk=invitation1.pk).status, "5")
		self.assertEqual(ReferralInvitation.objects.get(pk=invitation2.pk).status, "6")

		email = get_email(0)
		self.assertNotEqual(email.subject.find('has approve'), -1)

	def test_friend_process_view_accept_double(self):
		invitation1 = ReferralInvitation.objects.create(from_user=self.friend.user,
			to_user=self.test_healer.user,
			message="",
			status="2")

		response = self.client.get(reverse('friend_accept', args=['referrals', self.friend.user.id]))
		self.assertEqual(response.status_code, 302)
		response = self.client.get(reverse('friend_accept', args=['referrals', self.friend.user.id]))
		self.assertEqual(response.status_code, 302)

	def test_friend_process_view_decline(self):
		invitation = ReferralInvitation.objects.create(from_user=self.friend.user,
			to_user=self.test_healer.user,
			message="",
			status="2")

		response = self.client.get(reverse('friend_decline', args=['referrals', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(ReferralInvitation.objects.get(pk=invitation.pk).status, "6")

		email = get_email(0)
		self.assertNotEqual(email.subject.find('has decline'), -1)

	def test_friend_process_view_remove(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)

		response = self.client.get(reverse('friend_remove', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Clients.objects.are_friends(self.test_healer.user, self.friend.user))

	def test_friend_process_view_remove_referral(self):
		Referrals.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)

		response = self.client.get(
			reverse('friend_remove_referral', args=['referrals', self.test_healer.user.id, self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Referrals.objects.are_friends(self.friend.user, self.test_healer.user))

	def test_friend_process_view_approve(self):
		self.friend.approval_rating = 0
		self.friend.save()
		response = self.client.get(reverse('friend_approve', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=self.friend.user).count(), 1)
		self.assertEqual(Client.objects.get(pk=self.friend.pk).approval_rating, 100)

	def test_friend_process_view_approve_my_client(self):
		self.friend.approval_rating = 0
		self.friend.save()
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)

		response = self.client.get(reverse('friend_approve', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=self.friend.user).count(), 1)
		self.assertEqual(Client.objects.get(pk=self.friend.pk).approval_rating, 100)

	def test_friend_process_view_add_client(self):
		response = self.client.get(reverse('friend_add', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=self.friend.user).count(), 1)

	def test_friend_process_view_add_my_client(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)
		response = self.client.get(reverse('friend_add', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=self.friend.user).count(), 1)

	def test_friend_process_view_add_referral(self):
		self.friend = Healer.objects.get(pk=3)
		response = self.client.get(reverse('friend_add', args=['referrals', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertTrue(Referrals.objects.are_friends(self.test_healer.user, self.friend.user))

		email = get_email(0)
		self.assertTrue('is now Referring' in email.subject)

	def test_friend_process_view_add_as_client(self):
		self.friend = Healer.objects.get(pk=3)
		response = self.client.get(reverse('friend_add', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertTrue(Clients.objects.are_friends(self.test_healer.user, self.friend.user))

	def test_friend_process_view_add_referral_as_client(self):
		self.friend = Healer.objects.get(pk=3)
		Referrals.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)
		response = self.client.get(reverse('friend_add', args=['clients', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Clients.objects.are_friends(self.test_healer.user, self.friend.user))
		self.assertTrue(Referrals.objects.are_friends(self.test_healer.user, self.friend.user))

	def test_friend_process_view_add_client_as_referral(self):
		self.friend = Healer.objects.get(pk=3)
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.friend.user)
		response = self.client.get(reverse('friend_add', args=['referrals', self.friend.user.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Clients.objects.are_friends(self.test_healer.user, self.friend.user))
		self.assertTrue(Referrals.objects.are_friends(self.test_healer.user, self.friend.user))


class HealersAjaxTest(HealersTest):
	""" Ajax functions called directly without django test client """

	def setUp(self):
		# get client from fixture
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()

		self.test_client = Client.objects.get(pk=5)
		self.request = self.initialize_ajax_request(self.test_healer)
		self.rest_client = APIClient()
		self.rest_client.force_authenticate(user=self.test_healer.user)

		self.treatment_length = TreatmentTypeLength.objects.all()[0]

		healers.models.send_sms.reset_mock()


class AppointmentDeleteFutureAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(AppointmentDeleteFutureAjaxTest, self).setUp()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

		self.appointment = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date()+timedelta(days=9),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_count=10,
			location=Location.objects.get(pk=1),
			treatment_length=self.treatment_length)

	def test_invalid_appointment_id(self):
		response = appointment_delete(self.request,
			appointment="test",
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find") != -1)

	def test_not_found(self):
		response = appointment_delete(self.request,
			appointment=0,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_dates(self):
		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start='2011 02 12T16:30:00.000Z',
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_delete(self):
		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start+timedelta(days=4)),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertEqual(appt.end_date, self.start.date()+timedelta(days=3))
		self.assertEqual(appt.repeat_count, 4)

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.start.date()+timedelta(days=4))
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)

	def test_delete_from_first(self):
		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			timeout_id=None)

		appt = Appointment.objects.all()
		self.assertFalse(appt.count())

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.appointment.start_date)
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)

	def test_delete_from_second(self):
		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(days=1)),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertEqual(appt.end_date, self.start.date())
		self.assertTrue(appt.is_single())

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.appointment.start_date + timedelta(days=1))
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)

	def test_delete_weekly_from_second(self):
		self.appointment.delete()
		self.appointment = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date()+timedelta(weeks=9),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period = rrule.WEEKLY,
			repeat_count = 10,
			location=Location.objects.get(pk=1),
			treatment_length=self.treatment_length)

		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(weeks=1)),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertEqual(appt.end_date, self.start.date())
		self.assertTrue(appt.is_single())

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.appointment.start_date + timedelta(weeks=1))
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)

	def test_delete_from_last(self):
		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(datetime.combine(self.appointment.end_date, time())),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertEqual(appt.end_date, self.appointment.end_date - timedelta(days=1))
		self.assertEqual(appt.repeat_count, self.appointment.repeat_count-1)

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.appointment.end_date)
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)
		self.assertTrue(cancel_appt.is_single())

	def test_delete_from_before_last(self):
		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(days=8)),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertEqual(appt.end_date, self.start.date()+timedelta(days=7))
		self.assertEqual(appt.repeat_count, 8)

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.appointment.end_date-timedelta(days=1))
		self.assertEqual(cancel_appt.end_date, self.appointment.end_date)

	def test_delete_ongoing_converted(self):
		self.appointment.repeat_count = None
		self.appointment.end_date = None
		self.appointment.save()

		response = appointment_delete_future(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.appointment.start + timedelta(days=4)),
			timeout_id=None)

		appt = Appointment.objects.all()[0]
		self.assertTrue(appt.is_finite())
		self.assertEqual(appt.end_date, self.start.date()+timedelta(days=3))
		self.assertEqual(appt.repeat_count, 4)

		cancel_appt = Appointment.canceled_objects.all()[0]
		self.assertEqual(cancel_appt.start_date, self.start.date()+timedelta(days=4))
		self.assertTrue(cancel_appt.is_ongoing())

class AppointmentDeleteAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(AppointmentDeleteAjaxTest, self).setUp()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

		self.appointment = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=Location.objects.get(pk=1),
			treatment_length=self.treatment_length)

	def test_invalid_appointment_id(self):
		response = appointment_delete(self.request,
			appointment="test",
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find") != -1)


	def test_not_found(self):
		response = appointment_delete(self.request,
			appointment=0,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_dates(self):
		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start='2011 02 12T16:30:00.000Z',
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_invalid_all_slots(self):
		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots="end",
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_last_modified_by(self):
		settings.GET_NOW = lambda: create_test_time() + timedelta(days=1)

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		settings.GET_NOW = create_test_time

		appt = Appointment.canceled_objects.get(id=self.appointment.id)
		self.assertEqual(appt.created_by, self.appointment.created_by)
		self.assertEqual(appt.created_date, self.appointment.created_date)
		self.assertEqual(appt.last_modified_by, self.request.user)
		self.assertTrue(appt.last_modified_date > appt.created_date)

	def test_success(self):
		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertTrue(Appointment.canceled_objects.get(pk=self.appointment.id).canceled)

		email = get_email()
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertNotEqual(email.body.find('canceled'), -1)
		self.assertNotEqual(email.body.find(self.appointment.date_range_text()), -1)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)

	def test_delete_all_slots(self):
		self.appointment.repeat_period = rrule.WEEKLY
		self.appointment.repeat_count = 10
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=True,
			timeout_id=None)
		appts = Appointment.objects.all()
		self.assertEqual(appts.count(), 0)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_delete_single(self):
		self.appointment.repeat_period = rrule.WEEKLY
		self.appointment.repeat_count = 10
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(days=7)),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 1)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, (self.start + timedelta(days=7)).date())

		self.assertEqual(appts[0].base_appointment, r_appts[0])

		email = get_email(0)
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertEqual(email.body.find('Repeats'), -1)

	def test_delete_first_from_finite(self):
		self.appointment.repeat_period = rrule.WEEKLY
		self.appointment.repeat_count = 10
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 0)
		self.assertEqual(r_appts[0].start_date, (self.start + timedelta(days=7)).date())
		self.assertEqual(r_appts[0].repeat_count, 9)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, self.start.date())
		self.assertEqual(appts[0].repeat_period, None)

		self.assertEqual(appts[0].base_appointment, r_appts[0])

		email = get_email(0)
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertEqual(email.body.find('Repeats'), -1)

	def test_delete_last_from_finite(self):
		self.appointment.repeat_period = rrule.DAILY
		self.appointment.repeat_count = 10
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start+timedelta(days=9)),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 0)
		self.assertEqual(r_appts[0].repeat_count, 9)
		self.assertEqual(r_appts[0].end_date, (self.start + timedelta(days=8)).date())

	def test_delete_first_from_ongoing(self):
		self.appointment.repeat_period = rrule.WEEKLY
		self.appointment.repeat_count = 0
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 0)
		self.assertEqual(r_appts[0].start_date, (self.start + timedelta(days=7)).date())
		self.assertEqual(r_appts[0].repeat_count, 0)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, self.start.date())
		self.assertEqual(appts[0].repeat_period, None)

		self.assertEqual(appts[0].base_appointment, r_appts[0])

		email = get_email(0)
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertEqual(email.body.find('Repeats'), -1)

	def test_delete_last_one(self):
		self.appointment.repeat_period = rrule.DAILY
		self.appointment.repeat_count = 2
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(days=1)),
			all_slots=False,
			timeout_id=None)
		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		appts = Appointment.objects.all()
		self.assertEqual(appts.count(), 0)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 2)

	def test_delete_all_except_last(self):
		self.appointment.repeat_period = rrule.DAILY
		self.appointment.repeat_count = 3
		self.appointment.update_end_date()
		self.appointment.save()

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start + timedelta(days=1)),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 1)
		self.assertEqual(r_appts[0].repeat_count, 3)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, self.start.date() + timedelta(days=1))
		self.assertEqual(appts[0].repeat_period, None)

		response = appointment_delete(self.request,
			appointment=self.appointment.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)
		r_appts = Appointment.objects.all()
		self.assertEqual(r_appts.count(), 1)
		self.assertEqual(len(r_appts[0].exceptions), 1)
		self.assertEqual(r_appts[0].start_date, self.start.date() + timedelta(days=2))
		self.assertEqual(r_appts[0].end_date, self.start.date() + timedelta(days=2))
		self.assertEqual(r_appts[0].repeat_count, 1)

		appts = Appointment.canceled_objects.all()
		self.assertEqual(appts.count(), 2)

		for appt in appts:
			self.assertEqual(appt.base_appointment, r_appts[0])


class VacationTest(HealersTest):
	def setUp(self):
		super(VacationTest, self).setUp()
		self.start = create_test_time()

	def test_get_dates(self):
		vac = Vacation.objects.create(healer=self.test_healer,
			start_date=self.start.date() + timedelta(days=1),
			end_date=self.start.date() + timedelta(days=3),
			start_time=0,
			end_time=1440)

		dates = vac.get_dates()
		self.assertEqual(len(dates), 3)
		self.assertEqual(dates[0], vac.start_date)
		self.assertEqual(dates[1], self.start.date() + timedelta(days=2))
		self.assertEqual(dates[2], vac.end_date)


class AppointmentTest(HealersTest):
	def setUp(self):
		super(AppointmentTest, self).setUp()
		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

		self.appointment = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date() + timedelta(days=5),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=5,
			treatment_length=self.treatment_length)


	def test_find_available_dates_success(self):
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=6),
			end_date=self.end.date() + timedelta(days=6),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=7),
			end_date=self.end.date() + timedelta(days=9),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=3,
			exceptions=[get_timestamp(self.start.date() + timedelta(days=8))],
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=10),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=2,
			treatment_length=self.treatment_length)

		cmp_dates = [
			self.start + timedelta(days=8), # from exception
			self.start + timedelta(days=11),
			self.start + timedelta(days=13)
		]

		available_dates_dict = self.appointment.find_available_dates(3)
		dates = available_dates_dict['dates']
		self.assertEqual(len(dates), 3)
		for i, cmp_date in enumerate(cmp_dates):
			self.assertEqual(dates[i].date(), cmp_date.date())

	def test_find_available_dates_fail(self):
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=6),
			end_date=self.end.date() + timedelta(days=6),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=7),
			end_date=self.end.date() + timedelta(days=8),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=2,
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=9),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			treatment_length=self.treatment_length)

		dates = self.appointment.find_available_dates(2)
		self.assertEqual(dates, None)


class AppointmentNewFromContactAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(AppointmentNewFromContactAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(days=1, hours=1)
		self.end = self.start + timedelta(minutes=90)

	def test_contact_not_exist(self):
		response = appointment_new(self.request,
			client_id=0,
			client_type='contact',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("Could not find that contact.") != -1)

	def test_simple_contact(self):
		contact = Contact.objects.create(user=self.test_healer.user, name='First Last 1', email='test@healersource.com')
		response = appointment_new(self.request,
			client_id=contact.id,
			client_type='contact',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(), end_date=self.end.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].client.user.email, contact.email)
		self.assertEqual(appts[0].client.user.first_name, 'First')
		self.assertEqual(appts[0].client.user.last_name, 'Last 1')
		self.assertFalse(appts[0].client.user.has_usable_password())
		self.assertTrue(Clients.objects.are_friends(self.test_healer.user, appts[0].client.user))
		self.assertEqual(SiteJoinInvitation.objects.filter(from_user=self.test_healer.user, contact=contact).count(), 1)
		self.assertTrue(contact.users.count(), 1)

	def test_client_exist_and_not_my_client(self):
		Friendship.objects.all().delete()
		contact = Contact.objects.create(user=self.test_healer.user, name='First Last',
			email=self.test_client.user.email)
		response = appointment_new(self.request,
			client_id=contact.id,
			client_type='contact',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(), end_date=self.end.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].client, self.test_client)
		self.assertTrue(Clients.objects.are_friends(self.test_healer.user, appts[0].client.user))
		self.assertTrue(contact.users.count(), 1)

	def test_contact_without_email(self):
		contact = Contact.objects.create(user=self.test_healer.user, name='FirstNameOnly')
		response = appointment_new(self.request,
			client_id=contact.id,
			client_type='contact',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(), end_date=self.end.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].client.user.email, '')
		self.assertEqual(appts[0].client.user.first_name, 'FirstNameOnly')
		self.assertFalse(appts[0].client.user.has_usable_password())
		self.assertTrue(Clients.objects.are_friends(self.test_healer.user, appts[0].client.user))
		self.assertEqual(SiteJoinInvitation.objects.filter(from_user=self.test_healer.user, contact=contact).count(), 0)
		self.assertTrue(contact.users.count(), 1)


class AppointmentNewAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(AppointmentNewAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(days=1, hours=1)
		self.end = self.start + timedelta(minutes=90)

	def test_invalid_client_id(self):
		response = appointment_new(self.request,
			client_id='test',
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_client_not_exist(self):
		response = appointment_new(self.request,
			client_id=0,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("Could not find that client.") != -1)

	def test_invalid_dates(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start='2011 02 12T14:30:00.000Z',
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_invalid_location(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location="test",
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_invalid_treatment(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length="test",
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)
		self.assertTrue(load_message(response).find("invalid format") != -1)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=100,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_repeat_period(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=100,
			repeat_every=2,
			repeat_count=2,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)


	def test_invalid_repeat_every(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every="test",
			repeat_count=2,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)


	def test_invalid_repeat_count(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=2,
			repeat_count="test",
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_past_dates(self):
		start = create_test_time() - timedelta(days=1)
		end = start + timedelta(hours=2)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(start),
			end=to_timestamp(end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=2,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("Dates cannot be in the past.") != -1)

	def test_created_by(self):
		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		today = settings.GET_NOW().date()
		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(), end_date=self.end.date())[0]
		self.assertEqual(appts.created_by, self.request.user)
		self.assertEqual(appts.created_date.date(), today)
		self.assertEqual(appts.last_modified_by, self.request.user)
		self.assertEqual(appts.last_modified_date.date(), today)

	def test_conflict_single2vacation(self):
		Vacation.objects.create(healer=self.test_healer,
			start_date=self.start.date() - timedelta(days=1),
			end_date=self.end.date() + timedelta(days=1),
			start_time=0,
			end_time=14400)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("appointment during your time off") != -1)

	def test_conflict_ongoing2vacation(self):
		Vacation.objects.create(healer=self.test_healer,
			start_date=self.start.date() + timedelta(days=1),
			end_date=self.start.date() + timedelta(days=3),
			start_time=0,
			end_time=1440)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=2,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("appointment during your time off") != -1)


	def test_ongoing2single_success(self):
		confirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=3),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)

		unconfirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=4),
			end_date=self.end.date() + timedelta(days=4),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=False,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		#self.assertNotEqual(load_message(response).find("one or more conflicts"), -1)

		appts = Appointment.objects.filter(healer=self.test_healer, client=self.test_client,
			start_date=self.start.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].note, 'test')
		self.assertEqual(len(appts[0].exceptions), 1)
		self.assertFalse(Appointment.objects.filter(pk=unconfirmed_appt.pk).count())

		email = get_email(0)
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertEqual(email.to[0], unconfirmed_appt.client.user.email)

		email = get_email(1)
		self.assertNotEqual(email.subject.find('created'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_ongoing2single_unconfirmed_no_intersection(self):
		unconfirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=4),
			end_date=self.end.date() + timedelta(days=4),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=False,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		self.assertTrue(Appointment.objects.filter(pk=unconfirmed_appt.pk).count())

		email = get_email(0)
		self.assertNotEqual(email.subject.find('created'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_ongoing2finite_success(self):
		confirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=3),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=2,
			confirmed=True,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer, client=self.test_client,
			start_date=self.start.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].note, 'test')
		self.assertEqual(len(appts[0].exceptions), 2)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('created'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_ongoing2ongoing_conflict(self):
		confirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=3),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=None,
			confirmed=True,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		self.assertNotEqual(load_message(response).find("conflict with another repeating appointment"), -1)
		self.assertNotEqual(load_message(response).find(confirmed_appt.start_date.strftime("/%d")), -1)

	def test_finite2ongoing_conflict(self):
		confirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=3),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=None,
			confirmed=True,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=5,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		self.assertNotEqual(load_message(response).find("conflict with another repeating appointment"), -1)
		self.assertNotEqual(load_message(response).find(confirmed_appt.start_date.strftime("/%d")), -1)

	def test_finite_reduce(self):
		appt_single = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=2),
			end_date=self.end.date() + timedelta(days=2),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		appt_finite = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=4),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=2,
			confirmed=True,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=5,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		self.assertNotEqual(response.find("dlg_appt_reschedule_conflict_solving"), -1)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=5,
			conflict_solving=1,
			note='test',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer, start_date=self.start.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(len(appts[0].exceptions), 3)
		self.assertEqual(appts[0].repeat_count, 5)

	def test_finite_reschedule(self):
		appt_single = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=2),
			end_date=self.end.date() + timedelta(days=2),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		appt_finite = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() + timedelta(days=3),
			end_date=self.end.date() + timedelta(days=4),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=2,
			confirmed=True,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=4,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		self.assertNotEqual(response.find("dlg_appt_reschedule_conflict_solving"), -1)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=rrule.DAILY,
			repeat_every=1,
			repeat_count=4,
			conflict_solving=2,
			note='test',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer, start_date=self.start.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].repeat_count, 7)
		self.assertEqual(appts[0].end_date, appts[0].start_date + timedelta(days=6))
		self.assertEqual(len(appts[0].exceptions), 3)

	def test_single_success(self):
		unconfirmed_appt = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start) - 20,
			end_time=get_minutes(self.end) - 20,
			confirmed=False,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=1,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='test',
			timeout_id=None)

		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(), end_date=self.end.date())
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].note, 'test')

		email = get_email(1)
		self.assertNotEqual(email.subject.find('created'), -1)
		self.assertIn('have been booked', email.body)
		self.assertNotEqual(email.body.find(appts[0].date_range_text()), -1)
		self.assertNotEqual(email.body.find(Location.objects.get(pk=1).title), -1)
		self.assertEqual(email.body.find('Repeats'), -1)
		self.assertEqual(email.to[0], self.test_client.user.email)
		self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)

		self.assertFalse(Appointment.objects.filter(pk=unconfirmed_appt.pk).count())
		email = get_email(0)
		self.assertNotEqual(email.subject.find('declined'), -1)
		self.assertEqual(email.to[0], unconfirmed_appt.client.user.email)

	def test_single2single_conflict(self):
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=None,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_room_treatment_type_invalid(self):
		location = Location.objects.get(id=1)
		room = G(Room, location=location)
		self.treatment_length.treatment_type.rooms.add(
			G(Room, location=location)) # has another room

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=location.id,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None,
			room_id=room.id)

		self.assertIn('Invalid room for that treatment type', json.loads(response)['message'])

	def test_room_location_invalid(self):
		location = Location.objects.get(pk=1)
		location2 = Location.objects.get(pk=2)
		ClientLocation(client=self.test_healer, location=location).save()
		ClientLocation(client=self.test_healer, location=location2).save()
		room = G(Room, location=location)
		G(Room, location=location2)
		self.treatment_length.treatment_type.rooms.add(room)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=location2.id,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None,
			room_id=room.id)

		self.assertIn('Invalid room for that location', json.loads(response)['message'])

	def test_room_not_found(self):
		location = Location.objects.get(id=1)
		G(Room, location=location)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=location.id,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None,
			room_id=5)

		self.assertIn('Could not find that room', json.loads(response)['message'])

	def test_room_conflict(self):
		location = Location.objects.get(id=1)
		room = G(Room, location=location)

		create_appointment(healer=Healer.objects.get(pk=3),
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=location,
			treatment_length=self.treatment_length,
			room=room)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start),
			end=to_timestamp(self.end),
			location=location.id,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None,
			room_id=room.id)

		self.assertIn('conflict', json.loads(response)['message'])

	def test_single2ongoing_conflict(self):
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start + timedelta(days=7)),
			end=to_timestamp(self.end + timedelta(days=7)),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_single_before_ongoing_success(self):
		self.start = self.start + timedelta(days=2)
		self.end = self.end + timedelta(days=2)
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			treatment_length=self.treatment_length)

		response = appointment_new(self.request,
			client_id=self.test_client.id,
			client_type='client',
			start=to_timestamp(self.start - timedelta(days=1)),
			end=to_timestamp(self.end - timedelta(days=1)),
			location=None,
			treatment_length=self.treatment_length.id,
			repeat_period=None,
			repeat_every=None,
			repeat_count=None,
			conflict_solving=0,
			note='',
			timeout_id=None)

		self.assertEqual(load_message(response), '')

		appts = Appointment.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date())
		self.assertEqual(appts.count(), 1)


class AppointmentUpdateAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(AppointmentUpdateAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(days=1)
		self.end = self.start + timedelta(hours=2)
		self.create_appointment_data = {
			'healer': self.test_healer,
			'client': self.test_client,
			'start_date': self.start.date(),
			'end_date': self.end.date(),
			'start_time': get_minutes(self.start),
			'end_time': get_minutes(self.end),
			'location': None,
			'treatment_length': self.treatment_length
		}
		self.appointment = create_appointment(**self.create_appointment_data)

		self.update_appointment_data = {
			'request': self.request,
			'appointment': self.appointment.id,
			'start_old': to_timestamp(self.start),
			'end_old': to_timestamp(self.end),
			'start_new': to_timestamp(self.start),
			'end_new': to_timestamp(self.end),
			'treatment_length': self.appointment.treatment_length.id,
			'location_new': None,
			'note': '',
			'conflict_solving': 0,
			'all_slots': False,
			'timeout_id': None
		}

	def test_treatment_length_change_with_discount_code(self):
		# create code
		discount_code = DiscountCode.objects.create(code='CODE', healer=self.test_healer, amount=100)

		# add discount code to appointment
		data = self.update_appointment_data
		data['discount_code'] = discount_code.pk
		response = appointment_update(**data)

		# change length and set treatment length to None
		end = self.start + timedelta(hours=4)
		data = self.update_appointment_data
		data.update({
			'end_new': to_timestamp(end),
			'treatment_length': 0})

		response = appointment_update(**data)

	def test_invalid_appointment_id(self):
		data = self.update_appointment_data
		data['appointment'] = 'test'
		response = appointment_update(**data)
		self.assertIn('invalid format', load_message(response))

	def test_client_update(self):
		data = self.update_appointment_data
		data.update({
			'client_id': 4,
			'client_type': 'client'})
		response = appointment_update(**data)
		self.assertEqual(load_message(response), '')
		appointment = Appointment.objects.get(pk=self.appointment.id)
		self.assertEqual(appointment.client.id, 4)

	def test_client_update_not_found(self):
		data = self.update_appointment_data
		data.update({
			'client_id': 0,
			'client_type': 'client'})
 		response = appointment_update(**data)
		self.assertIn('not find', load_message(response))

	def test_not_found(self):
		self.appointment.delete()
		response = appointment_update(**self.update_appointment_data)
		self.assertIn('not find', load_message(response))

	def test_invalid_dates(self):
		data = self.update_appointment_data
		data['start_old'] = '2011 02 12T14:30:00.000Z'
 		response = appointment_update(**data)
 		self.assertIn('invalid format', load_message(response))

	def test_invalid_treatment(self):
		data = self.update_appointment_data
		data['treatment_length'] = 'test'
 		response = appointment_update(**data)
 		self.assertIn('invalid format', load_message(response))

		data['treatment_length'] = 100
 		response = appointment_update(**data)
 		self.assertIn('not find', load_message(response))

	def test_invalid_location(self):
		data = self.update_appointment_data
		data['location_new'] = 'test'
 		response = appointment_update(**data)
 		self.assertIn('invalid format', load_message(response))

	def test_invalid_all_slots(self):
		data = self.update_appointment_data
		data['all_slots'] = 'test'
 		response = appointment_update(**data)
 		self.assertIn('invalid format', load_message(response))

	def test_past_dates(self):
		start = create_test_time() - timedelta(days=1)
		end = start + timedelta(hours=2)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(start),
			'end_new': to_timestamp(end)})
 		response = appointment_update(**data)
 		self.assertEqual('Dates cannot be in the past.', load_message(response))

	def get_start_end(self, **kwargs):
		start = self.start + timedelta(**kwargs)
		end = self.end + timedelta(**kwargs)
		return start, end

	def test_first_instance_past_dates(self):
		self.appointment.repeat_period = rrule.WEEKLY
		self.appointment.repeat_every = 1
		self.appointment.end_date = None
		self.appointment.save()

		new_start, new_end = self.get_start_end(days=5)

		data = self.update_appointment_data
		data.update({
			'start_old': to_timestamp(self.start + timedelta(days=7)),
			'end_old': to_timestamp(self.end + timedelta(days=7)),
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'all_slots': True,
		})

		response = appointment_update(**data)
		self.assertEqual('Dates of first appointment cannot be in the past.', load_message(response))

	def test_single_conflict(self):
		new_start, new_end = self.get_start_end(hours=1)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date(),
			'end_date': new_end.date(),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end)})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end)})

   		response = appointment_update(**data)
		self.assertIn('conflict', load_message(response))

	def test_last_modified_by(self):
		settings.GET_NOW = lambda: create_test_time() + timedelta(days=1)

		new_start, new_end = self.get_start_end(days=1)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end)})

		appointment_update(**data)

		settings.GET_NOW = create_test_time

		appt = Appointment.objects.get(id=self.appointment.id)
		self.assertEqual(appt.created_by, self.appointment.created_by)
		self.assertEqual(appt.created_date, self.appointment.created_date)
		self.assertEqual(appt.last_modified_by, self.request.user)
		self.assertTrue(appt.last_modified_date > appt.created_date)

	def test_room_treatment_type_invalid(self):
		location = Location.objects.get(id=1)
		room = G(Room, location=location)
		self.treatment_length.treatment_type.rooms.add(
			G(Room, location=location)) # has another room

		response = appointment_update(self.request,
			self.appointment.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.start),
			end_new=to_timestamp(self.end),
			treatment_length=self.appointment.treatment_length.id,
			location_new=location.id,
			note='',
			conflict_solving=0,
			all_slots=False,
			timeout_id=None,
			room_id=room.id)

		self.assertIn('Invalid room for that treatment type', json.loads(response)['message'])

	def test_room_conflict(self):
		location = Location.objects.get(id=1)
		room = G(Room, location=location)

		create_appointment(healer=Healer.objects.get(pk=3),
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=location,
			treatment_length=self.treatment_length,
			room=room)

		response = appointment_update(self.request,
			self.appointment.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.start),
			end_new=to_timestamp(self.end),
			treatment_length=self.appointment.treatment_length.id,
			location_new=location.id,
			note='',
			conflict_solving=0,
			all_slots=False,
			timeout_id=None,
			room_id=room.id)

		self.assertIn('conflict', json.loads(response)['message'])

	def test_single_update_treatment(self):
		treatment = G(TreatmentType, healer=self.test_healer)
		treatment_length = G(TreatmentTypeLength, length=60,
			cost=10,
			treatment_type=treatment)

		new_start, new_end = self.get_start_end(days=1)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'treatment_length': treatment_length.id,
		})

   		response = appointment_update(**data)
		self.assertEqual('', load_message(response))

		appt = Appointment.objects.get(id=self.appointment.id)
		self.assertEqual(appt.start, new_start)
		self.assertEqual(appt.end, new_end)
		self.assertEqual(appt.treatment_length, treatment_length)


	def test_single_success(self):
		new_start, new_end = self.get_start_end(hours=1)

		data = self.create_appointment_data

		data.update({
			'start_date': new_start.date(),
			'end_date': new_end.date(),
			'start_time': get_minutes(new_start) - 20,
			'end_time': get_minutes(new_end) - 20,
			'confirmed': False,
		})

		unconfirmed_appt = create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
		})

   		response = appointment_update(**data)

		self.assertEqual(load_message(response), '')

		appointment = Appointment.objects.get(pk=self.appointment.id)
		self.assertEqual(appointment.start, new_start)
		self.assertEqual(appointment.note, 'test')

		email = get_email(0)
		self.assertIn('declined', email.subject)
		self.assertEqual(email.to[0], unconfirmed_appt.client.user.email)

		email = get_email(1)
		self.assertIn('updated', email.subject)
		self.assertIn('changed', email.body)
		self.assertIn(appointment.date_range_text(), email.body)
		self.assertIn(self.appointment.date_range_text(), email.body)
		self.assertIn(Location.objects.get(pk=1).title, email.body)

		self.assertFalse(Appointment.objects.filter(pk=unconfirmed_appt.pk).count())

	def set_appointment_repeat(self, every=1, count=None):
		self.appointment.repeat_period = rrule.DAILY
		self.appointment.repeat_every = every
		if count is None:
			self.appointment.end_date = None
		else:
			self.appointment.repeat_count = count
			self.appointment.update_end_date()
		self.appointment.save()

	def test_ongoing2single_success(self):
		self.set_appointment_repeat()
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date() + timedelta(days=1),
			'end_date': new_end.date() + timedelta(days=1),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
   		response = appointment_update(**data)
		self.assertEqual(load_message(response), '')

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].note, 'test')
		self.assertEqual(len(appts[0].exceptions), 1)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('updated'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_ongoing2finite_success(self):

		self.set_appointment_repeat()
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date() + timedelta(days=1),
			'end_date': new_end.date() + timedelta(days=1),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
			'repeat_period': rrule.DAILY,
			'repeat_every': 1,
			'repeat_count': 2,
		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
   		appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].note, 'test')
		self.assertEqual(len(appts[0].exceptions), 2)

		email = get_email(0)
		self.assertNotEqual(email.subject.find('updated'), -1)
		self.assertNotEqual(email.body.find('Repeats'), -1)

	def test_ongoing2ongoing_conflict(self):
		self.set_appointment_repeat()

		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date() + timedelta(days=1),
			'end_date': None,
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
			'repeat_period': rrule.DAILY,
			'repeat_every': 1,
		})
		appt = create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
   		response = appointment_update(**data)

		self.assertIn('conflict with another repeating appointment', load_message(response))
		self.assertIn(appt.start_date.strftime('/%d'), load_message(response))

	def test_finite2ongoing_conflict(self):
		self.set_appointment_repeat(count=3)
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date() + timedelta(days=1),
			'end_date': None,
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
			'repeat_period': rrule.DAILY,
			'repeat_every': 1,
		})
		appt = create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
		response = appointment_update(**data)

		self.assertIn('conflict with another repeating appointment', load_message(response))
		self.assertIn(appt.start_date.strftime('/%d'), load_message(response))

	def test_finite_reduce(self):
		self.set_appointment_repeat(count=5)
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date() + timedelta(days=2),
			'end_date': new_end.date() + timedelta(days=2),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		data.update({
			'start_date': new_start.date() + timedelta(days=3),
			'end_date': new_end.date() + timedelta(days=4),
			'repeat_period': rrule.DAILY,
			'repeat_every': 1,
			'repeat_count': 2,
		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
		response = appointment_update(**data)

		self.assertIn('dlg_appt_reschedule_conflict_solving', response)

		data.update({
			'conflict_solving': 1
		})
		response = appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(len(appts[0].exceptions), 3)
		self.assertEqual(appts[0].repeat_count, 2)

	def test_finite_reduce_update_dates(self):
		self.set_appointment_repeat(count=5)

		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date(),
			'end_date': new_end.date(),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		new_start, new_end = self.get_start_end(days=4, hours=3)

		data.update({
			'start_date': new_start,
			'end_date': new_end,
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(self.start + timedelta(hours=3)),
			'end_new': to_timestamp(self.end + timedelta(hours=3)),
			'location_new': 1,
			'note': 'test',
			'conflict_solving': 1,
			'all_slots': True,
		})
		appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(len(appts[0].exceptions), 2)
		self.assertEqual(appts[0].repeat_count, 3)
		self.assertEqual(appts[0].start_date, self.appointment.start_date + timedelta(days=1))
		self.assertEqual(appts[0].end_date, self.appointment.end_date - timedelta(days=1))

	def test_finite_reschedule(self):
		self.set_appointment_repeat(count=5)
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data

		# single
		data.update({
			'start_date': new_start.date() + timedelta(days=2),
			'end_date': new_end.date() + timedelta(days=2),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		# finite
		data.update({
			'start_date': new_start.date() + timedelta(days=3),
			'end_date': new_end.date() + timedelta(days=4),
			'repeat_period': rrule.DAILY,
			'repeat_every': 1,
			'repeat_count': 2,

		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'all_slots': True,
		})
		response = appointment_update(**data)

		self.assertIn('dlg_appt_reschedule_conflict_solving', response)

		data['conflict_solving'] = 2
		response = appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts[0].repeat_count, 8)
		self.assertEqual(appts[0].end_date, appts[0].start_date + timedelta(days=7))
		self.assertEqual(len(appts[0].exceptions), 3)

	def test_finite_reschedule_update_dates(self):
		self.set_appointment_repeat(count=5)
		new_start, new_end = self.get_start_end(hours=3)

		data = self.create_appointment_data
		data.update({
			'start_date': new_start.date(),
			'end_date': new_end.date(),
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'conflict_solving': 2,
			'all_slots': True,
		})
		appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts[0].repeat_count, 5)
		self.assertEqual(appts[0].start_date, self.appointment.start_date + timedelta(days=1))
		self.assertEqual(appts[0].end_date, self.appointment.end_date + timedelta(days=1))

	def test_finite_split_on_past(self):
		self.appointment.start_date = self.appointment.start_date - timedelta(days=7)
		self.set_appointment_repeat(every=2, count=10)

		new_start, new_end = self.get_start_end(hours=3)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'conflict_solving': 2,
			'all_slots': True,
		})
		appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, create_test_time().date())
		self.assertEqual(appts[0].end_date, self.appointment.end_date)
		self.assertEqual(appts[0].start_time, get_minutes(new_start))
		self.assertEqual(appts[0].repeat_count, 7)

		past_appts = Appointment.objects.filter(start_date=self.appointment.start_date)
		self.assertEqual(past_appts.count(), 1)
		self.assertEqual(past_appts[0].start_time, self.appointment.start_time)
		self.assertEqual(past_appts[0].end_date, create_test_time().date() - timedelta(days=2))
		self.assertEqual(past_appts[0].repeat_count, 3)

		self.assertEqual(appts[0].base_appointment, past_appts[0])

	def test_ongoing_split_on_past(self):
		self.appointment.start_date = self.appointment.start_date - timedelta(days=7)
		self.set_appointment_repeat(every=2)
		new_start, new_end = self.get_start_end(hours=3)

		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'location_new': 1,
			'note': 'test',
			'conflict_solving': 2,
			'all_slots': True,
		})
		appointment_update(**data)

		appts = Appointment.objects.filter(pk=self.appointment.pk)
		self.assertEqual(appts.count(), 1)
		self.assertEqual(appts[0].start_date, create_test_time().date())
		self.assertEqual(appts[0].end_date, None)
		self.assertEqual(appts[0].start_time, get_minutes(new_start))
		self.assertEqual(appts[0].repeat_count, 0)

		past_appts = Appointment.objects.filter(start_date=self.appointment.start_date)
		self.assertEqual(past_appts.count(), 1)
		self.assertEqual(past_appts[0].start_time, self.appointment.start_time)
		self.assertEqual(past_appts[0].end_date, create_test_time().date() - timedelta(days=2))
		self.assertEqual(past_appts[0].repeat_count, 3)

		self.assertEqual(appts[0].base_appointment, past_appts[0])

	def test_finite2single_reduce(self):
		self.set_appointment_repeat(count=5)
		new_start, new_end = self.get_start_end(days=1, minutes=360)

		data = self.create_appointment_data
		data.update({
			'start_date': self.appointment.start_date,
			'end_date': self.appointment.start_date,
			'start_time': self.appointment.start_time + 360,
			'end_time': self.appointment.end_time + 360,
		})
		create_appointment(**data)

  		data = self.update_appointment_data
		data.update({
			'start_old': to_timestamp(self.start + timedelta(days=1)),
			'end_old': to_timestamp(self.end + timedelta(days=1)),
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'note': 'test',
			'conflict_solving': 1,
			'all_slots': True,
		})
		appointment_update(**data)

		appt = Appointment.objects.get(pk=self.appointment.pk)
		self.assertEqual(len(appt.exceptions), 1)
		self.assertEqual(appt.repeat_count, 4)
		self.assertEqual(appt.start_date, self.appointment.start_date + timedelta(days=1))
		self.assertEqual(appt.end_date, self.appointment.end_date)

	def test_finite_first_convert_single(self):
		self.appointment.exceptions.append(get_timestamp((self.start + timedelta(days=1)).date()))
		self.set_appointment_repeat(count=5)
		new_start, new_end = self.get_start_end(minutes=360)

  		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'note': 'test',
		})
		appointment_update(**data)

		appt = Appointment.objects.get(start_date=self.appointment.start_date)
		self.assertEqual(appt.repeat_period, None)
		self.assertEqual(appt.repeat_count, 0)
		self.assertEqual(appt.end_date, appt.start_date)

		r_appt = Appointment.objects.get(pk=self.appointment.pk)
		self.assertEqual(r_appt.repeat_count, 3)
		self.assertEqual(r_appt.start_date, self.appointment.start_date + timedelta(days=2))
		self.assertEqual(r_appt.end_date, self.appointment.end_date)

		self.assertEqual(appt.base_appointment, r_appt)

	def test_finite_last_convert_single(self):
		self.appointment.exceptions.append(get_timestamp((self.start + timedelta(days=3)).date()))
		self.set_appointment_repeat(count=5)
		old_start, old_end = self.get_start_end(days=4)
		new_start, new_end = self.get_start_end(days=4, minutes=360)

  		data = self.update_appointment_data
		data.update({
			'start_old': to_timestamp(old_start),
			'end_old': to_timestamp(old_end),
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'note': 'test',
		})
		appointment_update(**data)

		r_appt = Appointment.objects.get(pk=self.appointment.pk)
		self.assertEqual(r_appt.end_date, self.appointment.end_date - timedelta(days=2))
		self.assertEqual(r_appt.repeat_count, self.appointment.repeat_count - 2)

		appt = Appointment.objects.get(start_date=self.appointment.start_date + timedelta(days=4))
		self.assertEqual(appt.repeat_count, 0)
		self.assertEqual(appt.end_date, appt.start_date)

		self.assertEqual(appt.base_appointment, r_appt)

	def test_ongoing_first_convert_single(self):
		self.appointment.exceptions.append(get_timestamp((self.start + timedelta(days=1)).date()))
		self.set_appointment_repeat()
		new_start, new_end = self.get_start_end(minutes=360)

  		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
			'note': 'test',
		})
		appointment_update(**data)

		appt = Appointment.objects.get(start_date=self.appointment.start_date)
		self.assertEqual(appt.repeat_period, None)
		self.assertEqual(appt.repeat_count, 0)
		self.assertEqual(appt.end_date, appt.start_date)

		r_appt = Appointment.objects.get(pk=self.appointment.pk)
		self.assertEqual(r_appt.repeat_count, 0)
		self.assertEqual(r_appt.start_date, self.appointment.start_date + timedelta(days=2))
		self.assertEqual(r_appt.end_date, self.appointment.end_date)

		self.assertEqual(appt.base_appointment, r_appt)

	def test_ongoing_first_convert_single_conflict(self):
		self.appointment.exceptions.append(get_timestamp((self.start + timedelta(days=1)).date()))
		self.set_appointment_repeat()
		new_start, new_end = self.get_start_end(minutes=360)

		data = self.create_appointment_data
		data.update({
			'start_time': get_minutes(new_start),
			'end_time': get_minutes(new_end),
		})
		create_appointment(**data)

  		data = self.update_appointment_data
		data.update({
			'start_new': to_timestamp(new_start),
			'end_new': to_timestamp(new_end),
		})
		response = appointment_update(**data)

		self.assertIn('conflict',load_message(response))

	def test_only_note_updated_no_email(self):
  		data = self.update_appointment_data
		data['note'] = 'test new note'
		response = appointment_update(**data)

		self.assertEqual(load_message(response), '')

		appointment = Appointment.objects.get(pk=self.appointment.id)
		self.assertEqual(appointment.note, 'test new note')
		self.assertEqual(count_emails(), 0)

	def test_repeat_only_note_updated_no_email(self):
		self.set_appointment_repeat(count=5)

  		data = self.update_appointment_data
		data.update({
			'note': 'test new note',
			'all_slots': True,
		})
		response = appointment_update(**data)

		self.assertEqual(load_message(response), '')

		appointment = Appointment.objects.get(pk=self.appointment.id)
		self.assertEqual(appointment.note, 'test new note')

		self.assertEqual(count_emails(), 0)

class ProfileReminderCommandTestCase(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'locations.json', 'modality.json']

	def setUp(self):
		Client.objects.get(pk=1).delete()
		self.test_healer = Healer.objects.create(user=User.objects.get(id=6), about='test')
		ClientLocation.objects.create(client=self.test_healer, location=Location.objects.all()[0])
		avatar = G(Avatar, user=self.test_healer.user)
		avatar.save()

	def call_command(self):
		args = []
		opts = {}
		call_command('send_profile_reminders', *args, **opts)

	def test_full_profile(self):
		modality = Modality.objects.get(pk=1)
		modality.healer.add(self.test_healer)

		self.test_healer.about = 'test'
		self.test_healer.save()
		self.call_command()
		self.assertEqual(count_emails(), 0)

	# def test_empty_location(self):
	# 	ClientLocation.objects.filter(client=self.test_healer).delete()
	#
	# 	self.call_command()
	# 	self.assertEqual(count_emails(), 1)

	def test_empty_avatar(self):
		Avatar.objects.filter(user=self.test_healer.user).delete()
		self.call_command()
		self.assertEqual(count_emails(), 1)

	def test_empty_about(self):
		self.test_healer.about = ''
		self.test_healer.save()

		self.call_command()
		self.assertEqual(count_emails(), 1)

	def test_in_interval(self):
		self.test_healer.about = ''
		self.test_healer.profile_completeness_reminder_lastdate = date.today() - timedelta(weeks=2)
		self.test_healer.profile_completeness_reminder_interval = 3
		self.test_healer.save()

		self.call_command()
		self.assertEqual(count_emails(), 0)

	def test_out_interval(self):
		self.test_healer.about = ''
		self.test_healer.profile_completeness_reminder_lastdate = date.today() - timedelta(weeks=2)
		self.test_healer.profile_completeness_reminder_interval = 1
		self.test_healer.save()

		self.call_command()
		self.assertEqual(count_emails(), 1)

	def test_double_sending(self):
		self.test_healer.about = ''
		self.test_healer.save()

		self.call_command()

		self.assertEqual(count_emails(), 1)
		self.test_healer = Healer.objects.get(id=self.test_healer.id)
		self.assertEqual(self.test_healer.profile_completeness_reminder_lastdate, date.today())

		self.call_command()
		self.assertEqual(count_emails(), 1) # remains the same

class AppointmentReminderCommandTestCase(HealersTest):

	def setUp(self):
		super(AppointmentReminderCommandTestCase, self).setUp()
		self.start = create_test_time() + timedelta(days=1)
		self.end = self.start + timedelta(hours=2)

		self.test_healer.send_reminders = True
		self.test_healer.save()
		self.test_client.send_reminders = True
		self.test_client.save()

	def test_client(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 1)

	def test_healer(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 1)

	def test_no_send_reminders(self):
		self.test_client.send_reminders = False
		self.test_client.save()

		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)

	def test_unconfirmed(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=False,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)

	def test_after_tomorrow(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date()+timedelta(days=1),
			end_date=self.end.date()+timedelta(days=1),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)

	def test_repeat(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() - timedelta(days=3),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=3,
			confirmed=True,
			treatment_length=self.treatment_length)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date() - timedelta(days=4),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.DAILY,
			repeat_every=3,
			confirmed=True,
			treatment_length=self.treatment_length)

		args = []
		opts = {}
		call_command('send_reminders', *args, **opts)

		self.assertEqual(count_emails(), 1)

class TimeslotNewAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeslotNewAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(days=1)
		self.end = self.start + timedelta(hours=2)

	def test_healer_not_found(self):
		self.test_healer.user.delete()
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_dates(self):
		response = timeslot_new(self.request,
			'2011 02 12T14:30:00.000Z',
			'2011 02 12T16:30:00.000Z',
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_invalid_end_date(self):
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date='2011 02 12T16:30:00.000Z',
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_invalid_location(self):
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id='test',
			weekly=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start,
			end_date=self.end,
			location=None).count(), 1)

	def test_invalid_weekly(self):
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly='test',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_same_day(self):
		start = create_test_time() + timedelta(hours=1)
		end = start + timedelta(days=1)

		response = timeslot_new(self.request,
			to_timestamp(start),
			to_timestamp(end),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("Dates cannot be on different days") != -1)

	def test_end_lte_start(self):
		start = create_test_time()
		end = start - timedelta(hours=2)

		response = timeslot_new(self.request,
			to_timestamp(start),
			to_timestamp(end),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("End must be after start") != -1)

	def test_end_date_lte_start(self):
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.start - timedelta(days=1)),
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("End must be after start") != -1)

	def test_weekly_success(self):
		timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date__isnull=True).count(), 1)

	def test_weekly_end_date_success(self):
		timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.end + timedelta(weeks=4)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=(self.end + timedelta(weeks=4)).date()).count(), 1)

	def test_weekly_next_week_success(self):
		timeslot_new(self.request,
			to_timestamp(self.start + timedelta(days=7)),
			to_timestamp(self.end + timedelta(days=7)),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date__isnull=True).count(), 1)

	def test_weekly_next_week_end_date_success(self):
		timeslot_new(self.request,
			to_timestamp(self.start + timedelta(days=7)),
			to_timestamp(self.end + timedelta(days=7)),
			end_date=to_timestamp(self.end + timedelta(weeks=4)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=(self.start + timedelta(days=7)).date(),
			end_date=(self.end + timedelta(weeks=4)).date()).count(), 1)

	def test_single_success(self):
		timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date()).count(), 1)

	def test_single_with_single_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_single_with_finite_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date() + timedelta(weeks=3),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start + timedelta(weeks=2)),
			to_timestamp(self.end + timedelta(weeks=2)),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") == -1)
		self.assertEqual(len(HealerTimeslot.objects.get(id=timeslot.id).exceptions), 1)

	def test_single_with_ongoing_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start + timedelta(weeks=2)),
			to_timestamp(self.end + timedelta(weeks=2)),
			end_date=None,
			location_id=None,
			weekly=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") == -1)
		self.assertEqual(len(HealerTimeslot.objects.get(id=timeslot.id).exceptions), 1)

	def test_ongoing_with_ongoing_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start - timedelta(weeks=2)),
			to_timestamp(self.end - timedelta(weeks=2)),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_ongoing_with_finite_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=(self.start + timedelta(weeks=1)).date(),
			end_date=(self.start + timedelta(weeks=2)).date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)
		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_ongoing_with_single_exception(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=(self.start + timedelta(weeks=1)).date(),
			end_date=(self.start + timedelta(weeks=1)).date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=None,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") == -1)

		timeslot = HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date__isnull=True)
		self.assertEqual(timeslot.count(), 1)
		# week 1 and  2
		self.assertEqual(len(timeslot[0].exceptions), 1)

	def test_finite_with_finite_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=(self.start + timedelta(weeks=1)).date(),
			end_date=(self.start + timedelta(weeks=2)).date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.start + timedelta(weeks=4)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_finite_with_single_exception(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=(self.start + timedelta(weeks=1)).date(),
			end_date=(self.start + timedelta(weeks=1)).date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=None,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.start + timedelta(weeks=4)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertNotIn('conflict', load_message(response))

		timeslot = HealerTimeslot.objects.filter(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=(self.start + timedelta(weeks=4)).date())
		self.assertEqual(timeslot.count(), 1)
		self.assertEqual(len(timeslot[0].exceptions), 1)

	def test_finite_before_ongoing(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=(self.start + timedelta(weeks=2)).date(),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.start + timedelta(weeks=1)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") == -1)

	def test_finite_with_ongoing_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=to_timestamp(self.start + timedelta(weeks=1)),
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_ongoing_with_finite_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=(self.start + timedelta(weeks=1)).date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None)

		self.assertTrue(load_message(response).find("conflict") != -1)

class TimeslotUpdateAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeslotUpdateAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(hours=1)
		self.end = self.start + timedelta(hours=2)

		self.new_start = self.start + timedelta(hours=5)
		self.new_end = self.end + timedelta(hours=5)

		self.timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			location=None)

	def test_not_found(self):
		id = self.timeslot.id
		self.timeslot.delete()
		response = timeslot_update(self.request,
			timeslot_id=id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)


	def test_invalid_dates(self):
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old='2011 02 12T14:30:00.000Z',
			end_old='2011 02 12T14:30:00.000Z',
			start_new='2011 02 12T14:30:00.000Z',
			end_new='2011 02 12T14:30:00.000Z',
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_single_new_dates(self):
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)

		start_date, start_time = get_date_minutes(self.new_start)
		self.assertEqual(HealerTimeslot.objects.get(pk=self.timeslot.id).start_date, start_date)
		self.assertEqual(HealerTimeslot.objects.get(pk=self.timeslot.id).start_time, start_time)

	def test_manual_to_weekly(self):
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=False,
			timeout_id=None)
		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.end_date, None)
		self.assertEqual(timeslot.repeat_period, rrule.WEEKLY)

	def test_manual_to_weekly_next_week(self):
		self.timeslot.start_date += timedelta(days=8)
		self.timeslot.end_date += timedelta(days=8)
		self.timeslot.save()
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.timeslot.start),
			end_old=to_timestamp(self.timeslot.end),
			start_new=to_timestamp(self.timeslot.start),
			end_new=to_timestamp(self.timeslot.end),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=False,
			timeout_id=None)
		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.start_date, self.timeslot.start_date)
		self.assertEqual(timeslot.end_date, None)
		self.assertEqual(timeslot.repeat_period, rrule.WEEKLY)

	def test_weekly_to_manual(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		next_week_delta = timedelta(days=7)
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start + next_week_delta),
			end_old=to_timestamp(self.end + next_week_delta),
			start_new=to_timestamp(self.new_start + next_week_delta),
			end_new=to_timestamp(self.new_end + next_week_delta),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.start_date, self.start.date())
		self.assertEqual(timeslot.exceptions[0], get_timestamp((self.start + next_week_delta).date()))

		new_timeslot = HealerTimeslot.objects.get(start_date=self.start + next_week_delta)
		self.assertEqual(new_timeslot.repeat_period, None)

	def test_weekly_update_all(self):
		exception = self.start.date() + timedelta(days=14)
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.exceptions = [get_timestamp(exception)]
		self.timeslot.save()

		next_week_delta = timedelta(days=7)
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start + next_week_delta),
			end_old=to_timestamp(self.end + next_week_delta),
			start_new=to_timestamp(self.new_start + next_week_delta + timedelta(days=1)),
			end_new=to_timestamp(self.new_end + next_week_delta + timedelta(days=1)),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=True,
			timeout_id=None)
		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.end_date, None)
		self.assertEqual(timeslot.start_date, self.new_start.date() + timedelta(days=1))
		self.assertEqual(timeslot.start_time, get_minutes(self.new_start))
		self.assertEqual(timeslot.repeat_period, rrule.WEEKLY)
		self.assertEqual(timeslot.exceptions, [get_timestamp(exception + timedelta(days=1))]) # exception shifted

	def test_weekly_update_single_exception(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		next_week_delta = timedelta(days=7)
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start + next_week_delta),
			end_old=to_timestamp(self.end + next_week_delta),
			start_new=to_timestamp(self.new_start + next_week_delta),
			end_new=to_timestamp(self.new_end + next_week_delta),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 2)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.start_date, self.start.date())
		self.assertEqual(len(timeslot.exceptions), 1)

		self.assertEqual(HealerTimeslot.objects.filter(start_date=(self.start + next_week_delta).date()).count(), 1)

	def test_weekly_update_single_first(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 2)

		next_week_delta = timedelta(days=7)
		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.repeat_period, rrule.WEEKLY)
		self.assertEqual(timeslot.start_date, (self.start + next_week_delta).date())
		self.assertEqual(timeslot.end_date, None)

		timeslot = HealerTimeslot.objects.get(start_date=self.start.date())
		self.assertEqual(timeslot.start_date, self.start.date())
		self.assertEqual(timeslot.end_date, self.start.date())
		self.assertEqual(timeslot.repeat_period, None)

	def test_single_conflict(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.new_start.date(),
			end_date=self.new_end.date(),
			start_time=get_minutes(self.new_start),
			end_time=get_minutes(self.new_end),
			location=None)

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("conflict") != -1)

	def test_single_ongoing_conflict(self):
		prev_week_start = self.new_start - timedelta(days=7)
		prev_week_end = self.new_end - timedelta(days=7)
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=prev_week_start.date(),
			end_date=None,
			start_time=get_minutes(prev_week_start),
			end_time=get_minutes(prev_week_end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("conflict") == -1)
		self.assertEqual(len(HealerTimeslot.objects.get(id=timeslot.id).exceptions), 1)

	def test_change_end_date(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		end_date = self.new_end + timedelta(weeks=3)
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=to_timestamp(end_date),
			weekly_new=True,
			all_slots=True,
			timeout_id=None)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.start_date, self.start.date())
		self.assertEqual(timeslot.end_date, end_date.date())

	def test_change_end_date_convert_to_single(self):
		self.timeslot.end_date = self.timeslot.start_date + timedelta(weeks=3)
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		end_date = self.timeslot.start + timedelta(days=3)
		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=to_timestamp(end_date),
			weekly_new=True,
			all_slots=True,
			timeout_id=None)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.repeat_period, None)
		self.assertEqual(timeslot.start_date, self.start.date())
		self.assertEqual(timeslot.end_date, self.start.date())

	def test_weekly_last_converted_to_single(self):
		self.timeslot.end_date = self.timeslot.start_date + timedelta(weeks=2)
		self.timeslot.exceptions = [get_timestamp(self.timeslot.start_date + timedelta(weeks=1))]
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=True,
			all_slots=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 2)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.repeat_period, None)
		self.assertEqual(timeslot.start_date, self.start.date() + timedelta(weeks=2))
		self.assertEqual(len(timeslot.exceptions), 0)

	def test_no_conflict_after_end_date(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		prev_start = self.new_start - timedelta(weeks=3)
		prev_end = self.new_end - timedelta(weeks=3)
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=prev_start.date(),
			end_date=(prev_end + timedelta(weeks=2)).date(),
			start_time=get_minutes(prev_start),
			end_time=get_minutes(prev_end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start),
			end_new=to_timestamp(self.new_end),
			start_date=None,
			end_date=None,
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("conflict") == -1)

	def test_no_conflict_before_start_date(self):
		self.timeslot.end_date = None
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.new_start.date(),
			end_date=None,
			start_time=get_minutes(self.new_start),
			end_time=get_minutes(self.new_end),
			repeat_period=rrule.WEEKLY,
			location=None)

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start),
			end_old=to_timestamp(self.end),
			start_new=to_timestamp(self.new_start - timedelta(weeks=4)),
			end_new=to_timestamp(self.new_end - timedelta(weeks=4)),
			start_date=None,
			end_date=to_timestamp(self.new_end - timedelta(days=1)),
			weekly_new=False,
			all_slots=False,
			timeout_id=None)
		self.assertTrue(load_message(response).find("conflict") == -1)

	def test_weekly_update_start_date(self):
		# call from next week after start
		self.timeslot.end_date = self.timeslot.start_date + timedelta(weeks=4)
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		response = timeslot_update(self.request,
			timeslot_id=self.timeslot.id,
			start_old=to_timestamp(self.start+timedelta(weeks=1)),
			end_old=to_timestamp(self.end+timedelta(weeks=1)),
			start_new=to_timestamp(self.new_start+timedelta(weeks=1)),
			end_new=to_timestamp(self.new_end+timedelta(weeks=1)),
			start_date=to_timestamp(self.start + timedelta(weeks=1)),
			end_date=to_timestamp(self.end + timedelta(weeks=4)),
			weekly_new=True,
			all_slots=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.repeat_period, rrule.WEEKLY)
		self.assertEqual(timeslot.start_date, (self.start + timedelta(weeks=1)).date())
		self.assertEqual(timeslot.end_date, self.timeslot.end_date)

class TimeslotDeleteFutureAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeslotDeleteFutureAjaxTest, self).setUp()
		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

	def create_timeslot(self, weekly=False):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date() if not weekly else None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY if weekly else None,
			location=None)
		return timeslot

	def test_invalid_dates(self):
		response = timeslot_delete_future(self.request,
			timeslot_id=1,
			start='2011 02 12T14:30:00.000Z',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_not_find(self):
		response = timeslot_delete_future(self.request,
			timeslot_id=1,
			start=to_timestamp(self.start),
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find timeslot") != -1)

	def test_delete(self):
		timeslot = self.create_timeslot(weekly=True)

		response = timeslot_delete_future(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start + timedelta(weeks=2)),
			timeout_id=None)

		timeslot = HealerTimeslot.objects.get(id=timeslot.id)
		self.assertEqual(timeslot.end_date, self.start.date() + timedelta(weeks=1))

	def test_delete_from_first(self):
		timeslot = self.create_timeslot(weekly=True)

		response = timeslot_delete_future(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start),
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 0)

	def test_delete_from_second(self):
		timeslot = self.create_timeslot(weekly=True)

		response = timeslot_delete_future(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start + timedelta(weeks=1)),
			timeout_id=None)

		timeslot = HealerTimeslot.objects.get(id=timeslot.id)
		self.assertEqual(timeslot.end_date, self.start.date())
		self.assertTrue(timeslot.is_single())

class TimeslotDeleteAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeslotDeleteAjaxTest, self).setUp()
		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

	def create_timeslot(self, weekly=False):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date() if not weekly else None,
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			repeat_period=rrule.WEEKLY if weekly else None,
			location=None)
		return timeslot

	def test_invalid_dates(self):
		response = timeslot_delete(self.request,
			timeslot_id=1,
			start='2011 02 12T14:30:00.000Z',
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)


	def test_not_find(self):
		response = timeslot_delete(self.request,
			timeslot_id=1,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find timeslot") != -1)

	def test_weekly_all_success(self):
		timeslot = self.create_timeslot(weekly=True)

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		response = timeslot_delete(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start),
			all_slots=True,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 0)

	def test_weekly_single_exception_success(self):
		timeslot = self.create_timeslot(weekly=True)

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		response = timeslot_delete(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start + timedelta(days=7)),
			all_slots=False,
			timeout_id=None)

		timeslot = HealerTimeslot.objects.get(id=timeslot.id)
		self.assertEqual(HealerTimeslot.objects.all().count(), 1)
		self.assertEqual(len(timeslot.exceptions), 1)

	def test_weekly_single_first_success(self):
		timeslot = self.create_timeslot(weekly=True)
		timeslot.exceptions = [get_timestamp(timeslot.start_date + timedelta(days=7))]
		timeslot.save()

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		response = timeslot_delete(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.filter(start_date=(self.start + timedelta(days=7)).date()).count(), 0)
		self.assertEqual(HealerTimeslot.objects.filter(start_date=(self.start + timedelta(days=14)).date()).count(), 1)

	def test_single_success(self):
		timeslot = self.create_timeslot(weekly=False)

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		response = timeslot_delete(self.request,
			timeslot_id=timeslot.id,
			start=to_timestamp(self.start),
			all_slots=False,
			timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 0)

	def test_weekly_last_converted_to_single(self):
		self.timeslot = self.create_timeslot(weekly=True)
		self.timeslot.end_date = self.timeslot.start_date + timedelta(weeks=2)
		self.timeslot.exceptions = [get_timestamp(self.timeslot.start_date + timedelta(weeks=1))]
		self.timeslot.repeat_period = rrule.WEEKLY
		self.timeslot.save()

		response = timeslot_delete(self.request,
								   timeslot_id=self.timeslot.id,
								   start=to_timestamp(self.start),
								   all_slots=False,
								   timeout_id=None)

		self.assertEqual(HealerTimeslot.objects.all().count(), 1)

		timeslot = HealerTimeslot.objects.get(id=self.timeslot.id)
		self.assertEqual(timeslot.repeat_period, None)
		self.assertEqual(timeslot.start_date, self.start.date() + timedelta(weeks=2))
		self.assertEqual(len(timeslot.exceptions), 0)


class TimeslotBookAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeslotBookAjaxTest, self).setUp()
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
		self.test_healer.save()
		self.request.user = self.test_client.user

		self.treatment_length.length = 45
		self.treatment_length.save()

		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

	def test_ivalid_timeslot(self):
		response = timeslot_book(self.request, "test", 0, self.treatment_length.id, self.test_client.id, '', '', None)
		self.assertTrue(load_message(response).find("invalid") != -1)

	def test_not_find_timeslot(self):
		response = timeslot_book(self.request, 0, 0, self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_client(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		response = timeslot_book(self.request, timeslot.id, 0, self.treatment_length.id, "test", '', '', None)

		self.assertTrue(load_message(response).find("invalid") != -1)

	def test_wrong_client(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))
		self.request.user = self.test_healer.user
		response = timeslot_book(self.request, timeslot.id, 0, self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("Wrong") != -1)

	def test_not_find_client(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		response = timeslot_book(self.request, timeslot.id, 0, self.treatment_length.id, 0, '', '', None)

		self.assertTrue(load_message(response).find("not find") != -1)

	def test_wrong_treatment(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))
		self.request.user = self.test_healer.user
		response = timeslot_book(self.request, timeslot.id, 0, "test", self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("Treatment type id in invalid format") != -1)

	def test_not_find_treatment(self):
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		response = timeslot_book(self.request, timeslot.id, 0, 100, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_start(self):
		start = create_test_time() + timedelta(hours=25)
		end = start + timedelta(hours=2)

		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		response = timeslot_book(self.request, timeslot.id, "",
			self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("Date in invalid format") != -1)

		response = timeslot_book(self.request, timeslot.id, to_timestamp(start - timedelta(minutes=5)),
			self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("Invalid start date") != -1)

		response = timeslot_book(self.request, timeslot.id, to_timestamp(start + timedelta(minutes=110)),
			self.treatment_length.id, self.test_client.id, '', '', None)
		self.assertTrue(load_message(response).find("Invalid start date") != -1)

	def test_ahead_days_fail(self):
		start = create_test_time() + timedelta(days=60)
		end = start + timedelta(hours=2)

		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		response = timeslot_book(self.request,
			timeslot.id,
			to_timestamp(timeslot.start),
			self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("can't book") != -1)

	def test_lead_time_fail(self):
		self.test_healer.leadTime = 2
		self.test_healer.save()
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		response = timeslot_book(self.request,
			timeslot.id,
			to_timestamp(timeslot.start),
			self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertIn('advance notice', load_message(response))

	def test_lead_time_tz_fail(self):
		self.test_healer.timezone = "+04:00"
		self.test_healer.leadTime = 2
		self.test_healer.save()
		self.start += timedelta(hours=3)
		self.end += timedelta(hours=3)
		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		response = timeslot_book(self.request,
			timeslot.id,
			to_timestamp(timeslot.start),
			self.treatment_length.id, self.test_client.id, '', '', None)

		self.assertTrue(load_message(response).find("advance notice") != -1)

	def test_success(self):
		start = create_test_time() + timedelta(days=2)
		end = start + timedelta(hours=2)

		timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		timeslot_book(self.request, timeslot.id, to_timestamp(start), self.treatment_length.id, self.test_client.id,
			'test', '', None)

		appointment = Appointment.objects.filter(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(start) + self.treatment_length.length)

		self.assertEqual(appointment.count(), 1)
		self.assertEqual(appointment[0].note, 'test')
		self.assertEqual(appointment[0].created_by, self.request.user)

		email = get_email()
		self.assertNotEqual(email.subject.find('created'), -1)
		self.assertNotEqual(email.body.find('created'), -1)
		self.assertEqual(email.to[0], appointment[0].healer.user.email)


class NewClientAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(NewClientAjaxTest, self).setUp()
		self.data = {'first_name': 'first_name',
				'last_name': 'last_name',
				'email': 'test@healersource.com',
				'phone': '2223322'}

	def new_client(self):
		response = self.rest_client.post(reverse('new_client'), {'data': urllib.urlencode(self.data)})
		return json.loads(response.content)

	def test_empty_first_name_fail(self):
		self.data['first_name'] = ''
		response = self.new_client()
		self.assertIn('first_name', response['error_elements'])

	def test_empty_email_success(self):
		self.data['email'] = ''
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 0)

	def test_invalid_email_fail(self):
		self.data['email'] = 'test'
		response = self.new_client()
		self.assertIn('email', response['error_elements'])

	def test_new_user(self):
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 1)

		email = get_email()
		self.assertNotEqual(email.subject.find('has added you as a Client'), -1)
		self.assertNotEqual(email.body.find(self.request.user.username), -1)

		client = Client.objects.get(user__email='test@healersource.com')
		self.assertEqual(client.user.first_name, self.data['first_name'])
		self.assertEqual(client.user.last_name, self.data['last_name'])
		self.assertEqual(client.phone_numbers.all()[0].number, self.data['phone'])
		self.assertEqual(client.approval_rating, 100)

	def test_existing_healer(self):
		healer2 = Healer.objects.get(pk=3)
		EmailAddress.objects.create(user=healer2.user, email=healer2.user.email, verified=True, primary=True)

		self.data['email'] = healer2.user.email
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 1)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=healer2.user).count(), 1)

	def test_existing_client(self):
		client2 = Client.objects.get(pk=5)
		EmailAddress.objects.create(user=client2.user, email=client2.user.email, verified=True, primary=True)

		self.data['email'] = client2.user.email
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 1)
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=client2.user).count(), 1)

	def test_dummy_user(self):
		email = 'dummy_user@healersource.com'
		user = User.objects.create(email=email, is_active=False)
		user.set_unusable_password()
		user.save()
		Client.objects.create(user=user)

		self.data['email'] = email
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 1)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.test_healer.user, contact__email=email,
			is_to_healer=False)
		self.assertEqual(invitation.count(), 0)

	def test_dummy_user_my_client(self):
		email = 'dummy_user@healersource.com'
		user = User.objects.create(email=email, is_active=False)
		user.set_unusable_password()
		user.save()
		Client.objects.create(user=user)
		Clients.objects.create(from_user=self.test_healer.user, to_user=user)

		self.data['email'] = email
		response = self.new_client()
		self.assertEqual(response['client']['has_email'], 1)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.test_healer.user, contact__email=email,
			is_to_healer=False)
		self.assertEqual(invitation.count(), 0)


# class NewBookingUnregisteredAjaxTest(HealersAjaxTest):
# 	store = None

# 	def setUp(self):
# 		super(NewBookingUnregisteredAjaxTest, self).setUp()
# 		self.request.user = AnonymousUser()

# 		self.treatment_length.length = 60
# 		self.treatment_length.save()

# 		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
# 		self.test_healer.save()
# 		start = create_test_time() + timedelta(days=2)
# 		end = start + timedelta(hours=2)

# 		self.timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
# 			start_date=start.date(),
# 			end_date=end.date(),
# 			start_time=get_minutes(start),
# 			end_time=get_minutes(end))

# 	def test_double_booking(self):
# 		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
# 		self.test_healer.save()

# 		data = {'first_name': 'firstname',
# 				'last_name': 'lastname',
# 				'email': 'test@healersource.com',
# 				'phone': '222-33-22',
# 				'note': 'test',
# 				'password1': '11111111',
# 				'password2': '11111111',
# 				'security_verification_0': self.store.hashkey,
# 				'security_verification_1': self.store.response,
# 				'referred_by': 'referrer',
# 				'start': to_timestamp(self.timeslot.start),
# 				'treatment_length': self.treatment_length.id,
# 				'timeslot': self.timeslot.id}

# 		response = appointment_new_unregistered(self.request, urllib.urlencode(data))
# 		self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed.'), -1)

# 		appointments = Appointment.objects.filter(healer=self.test_healer,
# 			start_date=self.timeslot.start_date,
# 			start_time=self.timeslot.start_time)
# 		self.assertEqual(appointments.count(), 1)

# 		challenge, response = conf.settings.get_challenge()()
# 		store = CaptchaStore.objects.create(challenge=challenge, response=response)

# 		data = {'first_name': 'firstname',
# 				'last_name': 'lastname',
# 				'email': 'test1@healersource.com',
# 				'phone': '222-33-22',
# 				'note': 'test',
# 				'password1': '11111111',
# 				'password2': '11111111',
# 				'security_verification_0': store.hashkey,
# 				'security_verification_1': store.response,
# 				'referred_by': 'referrer',
# 				'start': to_timestamp(self.timeslot.start),
# 				'treatment_length': self.treatment_length.id,
# 				'timeslot': self.timeslot.id}

# 		response = appointment_new_unregistered(self.request, urllib.urlencode(data))
# 		self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed.'), -1)

# 		appointments = Appointment.objects.filter(healer=self.test_healer,
# 			start_date=self.timeslot.start_date,
# 			start_time=self.timeslot.start_time)
# 		self.assertEqual(appointments.count(), 2)


# class NewBookingLoginAjaxTest(HealersAjaxTest):
# 	def setUp(self):
# 		super(NewBookingLoginAjaxTest, self).setUp()
# 		self.password = 123
# 		self.test_client.user.set_password(self.password)
# 		self.test_client.user.save()
# 		EmailAddress.objects.create(user=self.test_client.user, email=self.test_client.user.email, verified=True)
# 		self.request.user = AnonymousUser()
# 		self.request.session = SessionStore()

# 		start = create_test_time() + timedelta(days=2)
# 		end = start + timedelta(hours=2)
# 		self.timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
# 			start_date=start.date(),
# 			end_date=end.date(),
# 			start_time=get_minutes(start),
# 			end_time=get_minutes(end))

# 		self.treatment_length.length = 60
# 		self.treatment_length.save()

	# def test_invalid_timeslot_fail(self):
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': 'test',
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertEqual(response.find('appointment_new_unregistered_result'), -1)

	# def test_not_find_timeslot(self):
	# 	self.timeslot.delete()
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertEqual(response.find('appointment_new_unregistered_result'), -1)

	# def test_success(self):
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))

	# 	self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed.'), -1)

	# 	# check confirm link in email
	# 	email = get_email()
	# 	self.assertNotEqual(email.body.find(reverse('appointments')), -1)
	# 	self.assertNotEqual(email.subject.find('requested'), -1)
	# 	self.assertNotEqual(email.body.find('requested'), -1)

	# 	self.assertEqual(healers.models.send_sms.call_count, 2)

	# 	# check client invitation to healer
	# 	self.assertEqual(
	# 		ClientInvitation.objects.filter(from_user=self.test_client.user, to_user=self.test_healer.user).count(), 1)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 1)
	# 	self.assertFalse(appointments[0].confirmed)
	# 	self.assertEqual(appointments[0].note, 'test')

	# def test_success_my_client(self):
	# 	Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))

	# 	self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed.'), -1)

	# 	# check client invitation to healer
	# 	self.assertEqual(
	# 		ClientInvitation.objects.filter(from_user=self.test_client.user, to_user=self.test_healer.user).count(), 0)

	# 	email = get_email()
	# 	self.assertNotEqual(email.subject.find('requested'), -1)
	# 	self.assertNotEqual(email.body.find('requested'), -1)

	# 	self.assertEqual(healers.models.send_sms.call_count, 2)

	# def test_auto_confirmed_true(self):
	# 	self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
	# 	self.test_healer.save()
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertNotEqual(response.find('Your Appointment is confirmed, see you soon'), -1)

	# 	email = get_email()
	# 	# check no confirm link
	# 	self.assertEqual(email.body.find(reverse('appointments')), -1)
	# 	self.assertNotEqual(email.subject.find('created'), -1)

	# 	self.assertEqual(healers.models.send_sms.call_count, 0)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 1)
	# 	self.assertTrue(appointments[0].confirmed)
	# 	self.assertEqual(appointments[0].note, 'test')

	# def test_auto_confirmed_double_booking(self):
	# 	self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
	# 	self.test_healer.save()
	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertNotEqual(response.find('Your Appointment is confirmed, see you soon'), -1)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 1)

	# 	test_client2 = Client.objects.get(pk=4)
	# 	test_client2.user.set_password('111')
	# 	test_client2.user.save()

	# 	data = {'email': test_client2.user.email,
	# 			'password': '111',
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertNotEqual(response.find('Sadly, this time is no longer available'), -1)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 1)

	# def test_manual_confirm_double_booking(self):
	# 	self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL
	# 	self.test_healer.save()

	# 	data = {'email': self.test_client.user.email,
	# 			'password': self.password,
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed'), -1)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 1)

	# 	test_client2 = Client.objects.get(pk=4)
	# 	test_client2.user.set_password('111')
	# 	test_client2.user.save()
	# 	EmailAddress.objects.create(user=test_client2.user, email=test_client2.user.email, verified=True)

	# 	data = {'email': test_client2.user.email,
	# 			'password': '111',
	# 			'timeslot': self.timeslot.id,
	# 			'start': to_timestamp(self.timeslot.start),
	# 			'treatment_length': self.treatment_length.id,
	# 			'note': 'test'}

	# 	response = new_booking_login(self.request, urllib.urlencode(data))
	# 	self.assertNotEqual(response.find('Your Appointment has been requested, but is not yet confirmed.'), -1)

	# 	appointments = Appointment.objects.filter(healer=self.test_healer,
	# 		start_date=self.timeslot.start_date,
	# 		start_time=self.timeslot.start_time)
	# 	self.assertEqual(appointments.count(), 2)


class GetAppointmentsAjaxTest(HealersAjaxTest):
	def test_no_healer(self):
		self.request.user.id = 0

		response = getAppointments(self.request)
		self.assertNotEqual(response.find('not find'), -1)

	def test_success(self):
		start = create_test_time() + timedelta(days=1)
		end = start + timedelta(hours=2)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=None,
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=None,
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			location=None,
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date() + timedelta(days=21),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			repeat_count=3,
			location=None,
			treatment_length=self.treatment_length)

		response = getAppointments(self.request)
		response = json.loads(response)
		self.assertEqual(len(response['data']) / len(response['keys']), 3)

	def test_past_date_success(self):
		start = create_test_time() - timedelta(days=7)
		end = start + timedelta(hours=2)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=None,
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=None,
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			location=None,
			treatment_length=self.treatment_length)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date() + timedelta(days=21),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			repeat_count=3,
			location=None,
			treatment_length=self.treatment_length)

		# finite ended till today
		start = start - timedelta(days=28)
		end = end - timedelta(days=28)
		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date() + timedelta(days=21),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			repeat_every=1,
			repeat_count=3,
			location=None,
			treatment_length=self.treatment_length)

		response = getAppointments(self.request)
		response = json.loads(response)
		self.assertEqual(len(response['data']) / len(response['keys']), 2)


class GetTimeslotsEditAjaxTest(HealersAjaxTest):
	def test_no_healer(self):
		self.request.user.id = 0

		response = getTimeslotsEdit(self.request)
		self.assertNotEqual(response.find('not find'), -1)

	def test_success(self):
		start = create_test_time()
		end = start + timedelta(hours=2)
		location = Location.objects.get(pk=1)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=location,
			treatment_length=self.treatment_length)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date() + timedelta(days=1),
			end_date=end.date() + timedelta(days=1),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=location)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date() - timedelta(days=7),
			end_date=end.date() - timedelta(days=7),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=location)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date() - timedelta(days=7),
			end_date=None,
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY,
			location=location)

		response = getTimeslotsEdit(self.request)
		response = json.loads(response)
		self.assertEqual(len(response['data']) / len(response['keys']), 3)


class GetTimeslotsReadonlyAjaxTest(HealersAjaxTest):
	def test_no_healer(self):
		response = getTimeslotsReadonly(self.request, '')
		self.assertNotEqual(response.find('not find'), -1)

	def test_no_schedule_visible(self):
		self.test_healer.scheduleVisibility = Healer.VISIBLE_DISABLED
		self.test_healer.save()
		response = getTimeslotsReadonly(self.request, self.test_healer)
		self.assertNotEqual(response, '[]')

		self.request.user = None
		response = getTimeslotsReadonly(self.request, self.test_healer)
		self.assertNotEqual(response.find('"data": []'), -1)
		self.request.user = self.test_healer.user

	def test_now_filter(self):
		start = create_test_time().replace(hour=0) + timedelta(hours=-2)
		end = start + timedelta(hours=1)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		start1 = create_test_time().replace(hour=0) + timedelta(hours=1)
		end1 = start1 + timedelta(hours=1)
		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start1.date(),
			end_date=end1.date(),
			start_time=get_minutes(start1),
			end_time=get_minutes(end1))

		response = getTimeslotsReadonly(self.request, self.test_healer)
		response = json.loads(response)
		self.assertEqual(len(response['data']) / len(response['keys']), 1)

	def test_now_tz_filter(self):
		# healer local date in other day
		self.test_healer.timezone = "+12:00"
		self.test_healer.save()

		test_time = create_test_time().replace(hour=0) + timedelta(days=1)

		start = test_time + timedelta(hours=-2)
		end = start + timedelta(hours=1)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		start1 = test_time + timedelta(hours=7)
		end1 = start1 + timedelta(hours=1)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start1.date(),
			end_date=end1.date(),
			start_time=get_minutes(start1),
			end_time=get_minutes(end1))

		response = getTimeslotsReadonly(self.request, self.test_healer)
		response = json.loads(response)
		self.assertEqual(len(response['data']) / len(response['keys']), 1)

	def test_success(self):
		start = create_test_time()
		end = start + timedelta(hours=2)

		create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=start.date() + timedelta(days=1),
			end_date=end.date() + timedelta(days=1),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			treatment_length=self.treatment_length)

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date() + timedelta(days=2),
			end_date=end.date() + timedelta(days=2),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		UnavailableSlot.objects.create(healer=self.test_healer,
			api=GOOGLE_API,
			start_date=start.date() + timedelta(days=3),
			end_date=end.date() + timedelta(days=3),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		Vacation.objects.create(healer=self.test_healer,
			start_date=start.date() + timedelta(days=1),
			end_date=end.date() + timedelta(days=2),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date() - timedelta(days=6),
			end_date=None,
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			repeat_period=rrule.WEEKLY)

		response = getTimeslotsReadonly(self.request, self.test_healer)
		response = json.loads(response)
		#vacation splitted on 2 days + 2 healertimeslot + appointment + unavailable slot
		self.assertEqual(len(response['data']) / len(response['keys']), 6)


class GoogleCalendarViewsTest(HealersTest):
	def test_instruction_view_correct_response(self):
		response = self.client.get(reverse('google_calendar_instruction'))
		self.assertEqual(response.context['healer'], self.test_healer)
		self.assertEqual(response.status_code, 200)

	def test_disable_view_success(self):
		appointment = create_appointment(healer=self.test_healer,
			client=self.test_client,
			start_date=create_test_time().date(),
			end_date=create_test_time().date(),
			start_time=720,
			end_time=840,
			google_event_id='123',
			treatment_length=self.treatment_length)
		self.test_healer.google_calendar_id = '123'
		self.test_healer.google_email = 'test@healersource.com'
		self.test_healer.save()

		response = self.client.get(reverse('google_calendar_disable'))
		self.assertRedirects(response, reverse('google_calendar_instruction'), 302)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertFalse(self.test_healer.google_calendar_id)
		self.assertFalse(self.test_healer.google_email)

		self.assertFalse(Appointment.objects.get(pk=appointment.pk).google_event_id)


class TimeoffNewAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeoffNewAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(days=1)
		self.end = self.start + timedelta(hours=2)

	def test_healer_not_found(self):
		self.test_healer.user.delete()
		response = timeoff_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_dates(self):
		response = timeoff_new(self.request,
			'2011 02 12T14:30:00.000Z',
			'2011 02 12T16:30:00.000Z',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_end_lte_start(self):
		start = create_test_time()
		end = start - timedelta(hours=2)

		response = timeoff_new(self.request,
			to_timestamp(start),
			to_timestamp(end),
			timeout_id=None)

		self.assertTrue(load_message(response).find("End must be after start") != -1)

	def test_success(self):
		timeoff_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			timeout_id=None)

		timeslots = Vacation.objects.filter(healer=self.test_healer)
		self.assertEqual(len(timeslots), 1)
		self.assertEqual(timeslots[0].start, self.start)
		self.assertEqual(timeslots[0].end, self.end)

	def test_several_days_success(self):
		self.end += timedelta(days=2)
		timeoff_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			timeout_id=None)

		timeslots = Vacation.objects.filter(healer=self.test_healer)
		self.assertEqual(len(timeslots), 1)
		self.assertEqual(timeslots[0].start, self.start)
		self.assertEqual(timeslots[0].end, self.end)


class TimeoffUpdateAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeoffUpdateAjaxTest, self).setUp()
		self.start = create_test_time() + timedelta(hours=1)
		self.end = self.start + timedelta(hours=2)

		self.new_start = self.start + timedelta(hours=5)
		self.new_end = self.end + timedelta(hours=5)

		self.timeslot = Vacation.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

	def test_not_found(self):
		id = self.timeslot.id
		self.timeslot.delete()
		response = timeoff_update(self.request,
			timeslot_id=id,
			start=to_timestamp(self.new_start),
			end=to_timestamp(self.new_end),
			timeout_id=None)
		self.assertTrue(load_message(response).find("not find") != -1)

	def test_invalid_dates(self):
		response = timeoff_update(self.request,
			timeslot_id=self.timeslot.id,
			start='2011 02 12T14:30:00.000Z',
			end='2011 02 12T14:30:00.000Z',
			timeout_id=None)

		self.assertTrue(load_message(response).find("invalid format") != -1)

	def test_end_lte_start(self):
		start = create_test_time()
		end = start - timedelta(hours=2)

		response = timeoff_update(self.request,
			timeslot_id=self.timeslot.id,
			start=to_timestamp(start),
			end=to_timestamp(end),
			timeout_id=None)

		self.assertTrue(load_message(response).find("End must be after start") != -1)

	def test_success(self):
		timeoff_update(self.request,
			timeslot_id=self.timeslot.id,
			start=to_timestamp(self.new_start),
			end=to_timestamp(self.new_end),
			timeout_id=None)

		timeslots = Vacation.objects.filter(healer=self.test_healer)
		self.assertEqual(len(timeslots), 1)
		self.assertEqual(timeslots[0].start, self.new_start)
		self.assertEqual(timeslots[0].end, self.new_end)

	def test_several_days_success(self):
		self.new_end += timedelta(days=2)
		timeoff_update(self.request,
			timeslot_id=self.timeslot.id,
			start=to_timestamp(self.new_start),
			end=to_timestamp(self.new_end),
			timeout_id=None)

		timeslots = Vacation.objects.filter(healer=self.test_healer)
		self.assertEqual(len(timeslots), 1)
		self.assertEqual(timeslots[0].start, self.new_start)
		self.assertEqual(timeslots[0].end, self.new_end)


class TimeoffDeleteAjaxTest(HealersAjaxTest):
	def setUp(self):
		super(TimeoffDeleteAjaxTest, self).setUp()
		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)

	def test_not_find(self):
		response = timeoff_delete(self.request,
			timeslot_id=1,
			timeout_id=None)

		self.assertTrue(load_message(response).find("not find timeslot") != -1)

	def test_success(self):
		timeslot = Vacation.objects.create(healer=self.test_healer,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end))

		self.assertEqual(Vacation.objects.all().count(), 1)

		response = timeoff_delete(self.request,
			timeslot_id=timeslot.id,
			timeout_id=None)

		self.assertEqual(Vacation.objects.all().count(), 0)

"""
class GoogleCalendarTimezoneTest(HealersTest):

	def test_calendar_creation(self):
		google_calendar = GoogleCalendar(self.test_healer.user)
		for i in range(0,20):
			calendar = google_calendar.create_calendar_entry(title=Healer.GOOGLE_CALENDAR_TITLE,
															 summary='This calendar contains healersource appointments',
															 color='#528800')
			new_calendar = google_calendar.create_request(calendar)
			new_calendar = google_calendar.get(new_calendar.GetEditLink().href)
			print i, new_calendar.timezone.value
			google_calendar.delete(new_calendar.GetEditLink().href)
"""

"""
class GoogleCalendarSyncTest(HealersTest):
	def setUp(self):
		super(GoogleCalendarSyncTest, self).setUp()

		self.start = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(hours=1)
		self.end = self.start + timedelta(hours=3)
		self.test_client = Client.objects.get(pk=5)

	def tearDown(self):
		if self.test_healer.google_calendar_id:
			google_calendar = GoogleCalendar(self.test_healer.user)
			try:
				google_calendar.delete(self.test_healer.google_calendar_id)
			except gdata.service.RequestError as e:
				# Calendar not exist
				pass

	def test_google_calendar_sync_success(self):
		" Tests for google calendar operations, all tests in one function to avoid google limits "
		self.assertFalse(self.test_healer.google_calendar_id)

		# sync view no appointments success
		response = self.client.get(reverse('google_calendar_sync'), follow=True)

		self.assertRedirects(response, reverse('google_calendar_instruction'), 302)
		#self.assertNotEqual(response.content.find('synced'), -1)

		# sync view success
		appointment = create_appointment(healer=self.test_healer,
												 client=self.test_client,
												 start=self.start,
												 end=self.end,
												 location=None)

		response = self.client.get(reverse('google_calendar_sync'), follow=True)

		self.assertRedirects(response, reverse('google_calendar_instruction'), 302)
		#self.assertNotEqual(response.content.find('synced'), -1)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		appointment = Appointment.objects.get(pk=appointment.pk)
		self.assertTrue(self.test_healer.google_calendar_id)
		self.assertTrue(self.test_healer.google_email)
		self.assertTrue(appointment.google_event_id)

		# create appointment
		appointment = create_appointment(healer=self.test_healer,
												 client=self.test_client,
												 start=self.end + timedelta(hours=1),
												 end=self.end + timedelta(hours=2),
												 location=None)
		time.sleep(5)
		appointment = Appointment.objects.get(pk=appointment.pk)
		self.assertTrue(appointment.google_event_id)

		# update appointment
		appointment.end += timedelta(hours=3)
		appointment.save()
		time.sleep(5)
		appointment = Appointment.objects.get(pk=appointment.pk)

		google_calendar = GoogleCalendar(self.test_healer.user)
		feed = google_calendar.calendar_service.GetCalendarEventFeed(self.test_healer.google_calendar_feed_link)
		appointment_events = [event for event in feed.entry if event.extended_property[0].value == str(appointment.id)]
		self.assertEqual(len(appointment_events), 1)
		from dateutil import parser

		end = parser.parse(appointment_events[0].when[0].end_time)
		self.assertEqual(appointment.end, end.replace(tzinfo=None))

		# cancel appointment
		appointment.cancel()
		time.sleep(5)
		appointment = Appointment.canceled_objects.get(pk=appointment.pk)
		self.assertFalse(appointment.google_event_id)
		feed = google_calendar.calendar_service.GetCalendarEventFeed(self.test_healer.google_calendar_feed_link)
		appointment_events = [event for event in feed.entry if event.extended_property[0].value == str(appointment.id)]
		self.assertEqual(len(appointment_events), 0)

	def test_google_calendar_recreate_success(self):
		" Tests google calendar recreation, when calendar removed in google ui by user "

		# sync view success
		self.start = datetime.utcnow().replace(hour=13, second=0, microsecond=0) + timedelta(hours=1)
		self.end = self.start + timedelta(hours=3)
		appointment = create_appointment(healer=self.test_healer,
												 client=self.test_client,
												 start=self.start,
												 end=self.end,
												 location=None)

		response = self.client.get(reverse('google_calendar_sync'), follow=True)

		self.assertRedirects(response, reverse('google_calendar_instruction'), 302)
		#self.assertNotEqual(response.content.find('synced'), -1)

		# remove google calendar
		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		google_calendar = GoogleCalendar(self.test_healer.user)
		google_calendar.delete(self.test_healer.google_calendar_id)

		# update appointment
		appointment = Appointment.objects.get(pk=appointment.pk)
		appointment.end += timedelta(hours=3)
		appointment.save()
		time.sleep(5)
		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		appointment = Appointment.objects.get(pk=appointment.pk)

		feed = google_calendar.calendar_service.GetCalendarEventFeed(self.test_healer.google_calendar_feed_link)
		appointment_events = [event for event in feed.entry if event.extended_property[0].value == str(appointment.id)]
		self.assertEqual(len(appointment_events), 1)
		from dateutil import parser

		end = parser.parse(appointment_events[0].when[0].end_time)
		self.assertEqual(appointment.end, end.replace(tzinfo=None))
"""


class WcentersBaseTest(HealersTest):
	def setUp(self):
		super(WcentersBaseTest, self).setUp()
		self.wc = G(WellnessCenter, schedule_trial_started_date=None)
		self.wc.user.set_password('test')
		self.wc.user.save()
		self.assertTrue(self.login_with_center())
		self.request = self.initialize_ajax_request(self.wc)

	def login_with_center(self):
		return self.client.login(email=self.wc.user.email, password='test')

	def create_provider(self):
		counter = str(Healer.objects.all().count())
		data = {
			'first_name': 'test_first' + counter,
			'last_name': 'test_last' + counter,
			'email': 'test%s@hs.com' % counter
		}
		self.client.post(reverse('healer_create'), data)
		provider = Healer.objects.get(user__email=data['email'])
		provider.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
		provider.save()
		return provider

	def healer_confirm(self, user):
		from django.contrib.auth.tokens import default_token_generator
		from django.utils.http import int_to_base36
		uid = int_to_base36(user.id)
		token = default_token_generator.make_token(user)
		data = {'password1': '1', 'password2': '1'}
		return self.client.post(reverse('healer_confirm', kwargs={'uidb36': uid, 'key': token}), data)

	def login_with_provider(self, user):
		self.healer_confirm(user)
		return self.client.login(email=user.email, password='1')

	def create_location(self):
		response = self.client.post(reverse('location'),
				{'title': 'test',
				'addressVisibility': Healer.VISIBLE_EVERYONE,
				'address_line1': 'test',
				'address_line2': 'test',
				'postal_code': 'test',
				'city': 'test',
				'state_province': 'test',
				'country': 'test',
				'name': 'Room1',
				'book_online': '1'})
		location = Location.objects.get(title='test')
		return location, response

	def add_all_tts_to_providers(self, providers):
		for provider in providers:
			wc_tt = WellnessCenterTreatmentType.objects.create(healer=provider, wellness_center=self.wc)
			wc_tt.treatment_types = TreatmentType.objects.filter(healer=self.wc)

	def get_schedule_permission_object(self):
		return Permission.objects.get(codename='can_use_wcenter_schedule')

	def add_schedule_permission(self, healer):
		healer.user.user_permissions.add(self.get_schedule_permission_object())

	def remove_schedule_permission(self, healer):
		healer.user.user_permissions.remove(self.get_schedule_permission_object())

	def make_active(self, healer):
		user = healer.user
		user.is_active = True
		user.save()

	def wcenter_providers_list_providers_count(self, response):
		html = json.loads(response)['html']
		html = BeautifulSoup(html)
		providers = html.find_all(class_='provider-item')
		return len(providers)


class WcentersTest(WcentersBaseTest):
	def test_location_form(self):
		response = self.client.get(reverse('location'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['location_form']), LocationForm)
		self.assertEqual(type(response.context['room_form']), RoomForm)

	def test_location_no_book_online_and_color(self):
		response = self.client.get(reverse('location'))
		self.assertFalse(
			self.is_book_online_and_color_on_location_form(response))

	def test_create_location(self):
		location, response = self.create_location()
		self.assertEqual(response.status_code, 302)
		#self.assertEqual(ClientLocation.objects.filter(client=self.wc).count(), 1)
		# Check if default color order is reversed
		rooms = location.rooms.all()
		self.assertEqual(rooms.count(), 1)
		self.assertEqual(rooms[0].name, 'Default Room')
		self.assertEqual(location.color, LOCATION_COLOR_LIST[-1])

	def test_ensure_schedule_is_unavailable_before_adding_treatment_type_and_location(self):
		self.add_schedule_permission(self.wc)

		response = self.client.post(reverse('schedule'))
		self.assertNotIn('<div class="schedule-provider-select">', response.content)
		self.assertIn('You must add at least one Treatment Type', response.content)

		#add treatment type and length
		treatment_type = G(TreatmentType, healer=self.wc.healer)
		G(TreatmentTypeLength, treatment_type=treatment_type)
		response = self.client.post(reverse('schedule'))
		self.assertNotIn('<div class="schedule-provider-select">', response.content)
		self.assertIn('You must add at least one Location', response.content)

		self.create_location()
		response = self.client.post(reverse('schedule'))
		self.assertNotIn('You must add at least one Location',  response.content)
		self.assertNotIn('<div class="schedule-provider-select">', response.content)

		self.create_provider()
		response = self.client.post(reverse('schedule'))
		self.assertIn('<div class="schedule-provider-select">', response.content)

	def test_provider_schedule_settings_menu(self):
		provider1 = self.create_provider()
		provider2 = self.create_provider()
		response = self.client.post(reverse('home'))

		html = BeautifulSoup(response.content)
		settings_links = html.find(id='provider_schedule_settings').find_all('a')
		self.assertEqual(settings_links[0].string, str(self.wc.user.client))
		self.assertIn(reverse('schedule_settings'), settings_links[0]['href'])

		self.assertEqual(settings_links[1].string, str(provider1.user.client))
		self.assertIn(reverse('schedule_settings', args=[provider1.user.username]), settings_links[1]['href'])

		self.assertEqual(settings_links[2].string, str(provider2.user.client))
		self.assertIn(reverse('schedule_settings', args=[provider2.user.username]), settings_links[2]['href'])


class WcentersScheduleTest(WcentersBaseTest):
	def setUp(self):
		def add_permissions():
			map(self.add_schedule_permission, [self.wc, self.provider1,
				self.provider2])
			map(self.make_active, [self.provider1, self.provider2])

		super(WcentersScheduleTest, self).setUp()
		self.location = self.create_location()[0]
		self.start = create_test_time() + timedelta(days=2)
		self.end = self.start + timedelta(hours=3)

		# create providers and treatment type length, assign it to providers
		self.provider1 = self.create_provider()
		self.provider2 = self.create_provider()

		add_permissions()

		self.tt = G(TreatmentType, healer=self.wc)
		self.ttl = G(TreatmentTypeLength, treatment_type=self.tt, length=60, cost='50')

		self.add_all_tts_to_providers([self.provider1, self.provider2])

	def create_availability(self, healer):
		return create_timeslot(healer, self.start, self.end, location=self.location)

	def test_price(self):
		ttl2 = G(TreatmentTypeLength, treatment_type=self.tt, length=60, cost='100')
		self.create_availability(self.provider1)

		wctl1 = WellnessCenterTreatmentTypeLength.objects.create(
					wellness_center=self.wc, healer=self.provider1)
		wctl2 = WellnessCenterTreatmentTypeLength.objects.create(
					wellness_center=self.wc, healer=self.provider2)

		wctl1.treatment_type_lengths.add(self.ttl)
		wctl2.treatment_type_lengths.add(ttl2)

		# use ttl2 here because ttl1.pk == tt.pk which makes test pass even though it shouldn't
		response = load_wcenter_providers(self.request, self.wc.pk, ttl2.pk)
		treatment_type_lengths = json.loads(response)['treatment_type_lengths']
		self.assertEqual(json.loads(treatment_type_lengths.values()[0])['cost'], '50')

	def test_wcenter_providers_list(self):
		response = load_wcenter_providers(self.request, self.wc.pk, self.ttl.pk)
		# make sure that no providers are listed because none of them have availability setup
		self.assertEqual(self.wcenter_providers_list_providers_count(response), 0)

		self.create_availability(self.provider1)
		self.create_availability(self.provider2)

		response = load_wcenter_providers(self.request, self.wc.pk, self.ttl.pk)
		self.assertEqual(self.wcenter_providers_list_providers_count(response), 2)

	def test_booking_availability(self):
		def get_availability_counter():
			data = json.loads(response)
			slots = json.loads(data['timeslot_list'])
			n = len(slots['keys'])
			return len(slots['data']) / n

		response = load_wcenter_schedule_data(self.request, self.provider1.pk, self.wc.pk, self.tt.pk)
		self.assertEqual(get_availability_counter(), 0)

		# create availabilities
		self.create_availability(self.provider1)

		response = load_wcenter_schedule_data(self.request, self.provider1.pk, self.wc.pk, self.tt.pk)
		self.assertEqual(get_availability_counter(), 1)

		# create private availability
		create_timeslot(self.provider1, self.start + timedelta(days=1), self.end + timedelta(days=1))

		# make sure private availabilities are being ignored
		response = load_wcenter_schedule_data(self.request, self.provider1.pk, self.wc.pk, self.tt.pk)
		self.assertEqual(get_availability_counter(), 1)

	def test_room_selection_when_booking(self):
		def book(provider):
			ts = self.create_availability(provider)
			response = timeslot_book(self.request, ts.id, to_timestamp(self.start), ttl.id,
				self.test_client.id, '', '', None)
			self.assertEqual(json.loads(response)['title'], 'Appointment Scheduled')
			appointment = Appointment.objects.get(healer=provider,
				client=self.test_client,
				start_date=self.start.date(),
				start_time=get_minutes(self.start),
				end_time=get_minutes(self.start) + ttl.length)

			return appointment.room.id

		def add_permissions():
			map(self.add_schedule_permission, [self.provider3, self.provider4])
			map(self.make_active, [self.provider3, self.provider4])

		room1 = Room.objects.get(name='Default Room')
		room2 = G(Room, location=self.location, name='Room2')
		room3 = G(Room, location=self.location, name='Room3')
		room4 = G(Room, location=self.location, name='Room4')

		self.provider3 = self.create_provider()
		self.provider4 = self.create_provider()

		add_permissions()

		self.tt = G(TreatmentType, healer=self.wc)
		tt2 = G(TreatmentType, healer=self.wc)
		tt3 = G(TreatmentType, healer=self.wc)
		tt4 = G(TreatmentType, healer=self.wc)
		tt5 = G(TreatmentType, healer=self.wc)

		self.tt.rooms = [room1, room3]
		tt2.rooms = [room1, room2, room4]
		tt3.rooms = [room1, room2]
		tt4.rooms = [room1, room4]

		ttl = G(TreatmentTypeLength, treatment_type=tt5, length=60)

		self.add_all_tts_to_providers([self.provider1, self.provider2,
			self.provider3, self.provider4])

		# enable client
		self.test_client = Client.objects.get(pk=5)
		self.request.user = self.test_client.user

		room_priority_1 = book(self.provider1)
		self.assertEqual(room_priority_1, room1.pk)
		room_priority_2 = book(self.provider2)
		self.assertIn(room_priority_2, [room2.pk, room4.pk])
		room_priority_3 = book(self.provider3)
		self.assertIn(room_priority_3, [room2.pk, room4.pk])
		room_priority_4 = book(self.provider4)
		self.assertEqual(room_priority_4, room3.pk)

	def test_add_availability_no_access(self):
		response = timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=None,
			weekly=True,
			timeout_id=None,
			username=self.provider2.user.username)

		self.assertEqual(json.loads(response)['message'], "You don't have permission to add availability for this location.")


class WcentersAppointmentsTest(WcentersBaseTest):
	def setUp(self):
		super(WcentersAppointmentsTest, self).setUp()
		self.location, _ = self.create_location()
		provider1 = self.create_provider()
		provider2 = self.create_provider()
		self.provider3 = self.create_provider()

		self.create_provider_appointment(provider1)
		self.create_provider_appointment(provider2)
		self.create_provider_appointment(self.provider3, confirmed=False)

	def create_provider_appointment(self, provider, confirmed=True, additional_time=None):
		self.test_healer = provider
		time = create_test_time()
		if additional_time:
			time += additional_time
		self.create_appt(time, location=self.location, confirmed=confirmed, include_end_date=True)

	def test_appointment_history(self):
		response = self.client.get(reverse('appointment_history'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['appointment_list']), 2)

	def test_confirmed_appointments(self):
		response = self.client.get(reverse('current_confirmed_appointments'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['appointments']), 2)

	def test_unconfirmed_appointments(self):
		response = self.client.get(reverse('schedule'))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['unconfirmed_appt_list']), 1)

	def test_decline_all(self):
		self.create_provider_appointment(self.provider3, confirmed=False, additional_time=timedelta(days=1))
		response = self.client.get(reverse('appointment_wcenter_confirm_decline_all', args=['decline']))
		self.assertEqual(response.status_code, 302)
		self.assertFalse(Appointment.objects.filter(healer=self.provider3).exists())

	def test_confirm_all(self):
		self.create_provider_appointment(self.provider3, confirmed=False, additional_time=timedelta(days=1))
		response = self.client.get(reverse('appointment_wcenter_confirm_decline_all', args=['confirm']))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(Appointment.objects.filter(healer=self.provider3, confirmed=True).count(), 2)


class WcentersProviderSettings(WcentersBaseTest):
	def setUp(self):
		super(WcentersProviderSettings, self).setUp()
		self.location, _ = self.create_location()
		self.provider = self.create_provider()
		self.tt = G(TreatmentType, healer=self.wc)

	def test_treatment_type_setup(self):
		response = self.client.post(reverse('save_wcenter_treatment_types', args=[self.provider.user.username]), {
				'wcenter_id': self.wc.id,
				'types': json.dumps([self.tt.id]),
		})

		self.assertEqual(response.status_code, 302)
		self.assertIn(self.tt, self.provider.wellness_center_treatment_types.get(
			wellness_center=self.wc).treatment_types.all())

	def test_vacation(self):
		def get_vacations():
			return Vacation.objects.filter(healer=self.provider,
				start_date=start.date(), end_date=end.date())

		start = create_test_time()
		end = start + timedelta(days=1)

		response = self.client.post(reverse('vacation', args=[self.provider.user.username]),
				{'start_0': start.strftime('%m/%d/%Y'),
				'start_1': start.strftime('%I:%M%p'),
				'end_0': end.strftime('%m/%d/%Y'),
				'end_1': end.strftime('%I:%M%p')})

		self.assertEqual(response.status_code, 200)

		vacations = get_vacations()
		self.assertEqual(vacations.count(), 1)

		# test vacation delete
		response = self.client.post(reverse('vacation_delete', args=[vacations[0].pk]))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(get_vacations().count(), 0)

	def test_set_schedule_visibility(self):
		# make sure it's not set up as default
		self.assertNotEqual(self.provider.scheduleVisibility, Healer.VISIBLE_EVERYONE)
		self.client.post(reverse('set_schedule_visibility', kwargs={'visibility': 'everyone',
			'username': self.provider.user.username}))

		# update provider record
		self.provider = Healer.objects.get(pk=self.provider.pk)

		self.assertEqual(self.provider.scheduleVisibility, Healer.VISIBLE_EVERYONE)


class WcentersProviderTest(WcentersBaseTest):
	def setUp(self):
		super(WcentersProviderTest, self).setUp()
		self.provider = self.create_provider()

		self.create_location()
		self.wc_treatment_type = G(TreatmentType, healer=self.wc.healer, title='treatment_type1')

		result_login = self.login_with_provider(self.provider.user)
		self.assertTrue(result_login)

	def test_treatment_type_setup(self):
		response = self.client.post(reverse('save_wcenter_treatment_types', args=[self.provider.user.username]), {
				'wcenter_id': self.wc.id,
				'types': json.dumps([self.wc_treatment_type.id]),
		})

		self.assertEqual(response.status_code, 302)
		self.assertIn(self.wc_treatment_type, self.provider.wellness_center_treatment_types.get(
			wellness_center=self.wc).treatment_types.all())

	def test_copy_my_treatment_types(self):
		# add treatment types to provider
		tt1 = G(TreatmentType, healer=self.provider, title='Treatment_Type1')
		tt2 = G(TreatmentType, healer=self.provider)

		tl1 = G(TreatmentTypeLength, treatment_type=tt1)
		tl2 = G(TreatmentTypeLength, treatment_type=tt2)

		response = self.client.get(reverse('copy_my_treatment_types', args=[self.wc.id]))
		self.assertEqual(response.status_code, 302)
		# one of the treatment types has to be ignored because the name is the same (case is being ignored)
		self.assertEqual(self.wc.healer_treatment_types.count(), 2)
		# the treatment type duplicate with the same name has to be created
		self.assertEqual(self.wc.healer_treatment_types.filter(title=tt2.title).count(), 1)

		# the treatment type has to be added (checked) for this provider at this wc
		duplicated_tt = self.wc.healer_treatment_types.get(title=tt2.title)
		all_providers_tts = self.provider.wellness_center_treatment_types.get(
					wellness_center=self.wc).treatment_types.all()
		self.assertIn(duplicated_tt, all_providers_tts)

		# first treatment type has to be checked as well
		not_duplicated_tt = self.wc.healer_treatment_types.get(title__iexact=tt1.title)
		self.assertIn(not_duplicated_tt, all_providers_tts)

		# treatment lengths has to be duplicated as well
		self.assertEqual(duplicated_tt.lengths.filter(length=tl2.length, cost=tl2.cost).count(), 1)

		# treatment lengths for existing treatment type have to be ignored
		self.assertFalse(not_duplicated_tt.lengths.filter(length=tl1.length, cost=tl1.cost).exists())

		email = get_email(1)
		self.assertIn(str(self.provider.user.client), email.subject)
		self.assertEqual(email.to[0], self.wc.user.email)
		self.assertIn(tt2.title, email.body)
		self.assertNotIn(tt1.title, email.body)
		self.assertIn(str(tl2), email.body)
		self.assertNotIn(str(tl1), email.body)


class WcentersCreateProviderTest(WcentersBaseTest):
	def setUp(self):
		super(WcentersCreateProviderTest, self).setUp()
		self.provider_data = {
			'first_name': 'test1',
			'last_name': 'test2',
			'email': 'test@hs.com'
		}

	def test_not_wellness_center(self):
		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)
		response = self.client.get(reverse('healer_create'))
		self.assertEqual(response.status_code, 404)

	def test_provider_exist(self):
		self.provider_data['email'] = self.test_healer.user.email
		response = self.client.post(reverse('healer_create'), self.provider_data)
		self.assertEqual(response.status_code, 302)
		self.assertIn(self.wc.user, [o['friend'] for o in Referrals.objects.referrals_to(self.test_healer.user)])
		self.assertNotIn(self.wc, self.test_healer.wellness_center_permissions.all())
		self.assertEqual(count_emails(), 1)

	def test_client_exist(self):
		data = self.provider_data
		data.update({
			'email': self.test_client.user.email
		})
		response = self.client.post(reverse('healer_create'), data)
		self.assertEqual(response.status_code, 302)
		h = Client.objects.get(id=self.test_client.id).healer
		self.assertIn(self.wc.user, [o['friend'] for o in Referrals.objects.referrals_to(h.user)])
		self.assertNotIn(self.wc, h.wellness_center_permissions.all())
		self.assertEqual(count_emails(), 1)

	def test_add_wellness_center_permission(self):
		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)
		self.client.get(reverse('add_wellness_center_permission', args=[self.wc.user.username]))
		self.assertIn(self.wc, self.test_healer.wellness_center_permissions.all())

	def test_post_and_confirm(self):
		dummy_user = User.objects.create(email='test@hs.com', username='12344567', is_active=False)
		dummy_user.set_unusable_password()
		dummy_user.save()
		Client.objects.create(user=dummy_user)

		response = self.client.post(reverse('healer_create'), self.provider_data)
		self.assertEqual(response.status_code, 302)

		h = Healer.objects.get(user__email=self.provider_data['email'])
		self.assertEqual(h.user.first_name, self.provider_data['first_name'])
		self.assertFalse(h.user.has_usable_password())
		self.assertFalse(h.user.is_active)
		self.assertIn(self.wc, h.wellness_center_permissions.all())

		self.assertIn(self.wc.user, [o['friend'] for o in Referrals.objects.referrals_to(h.user)])
		self.assertFalse(EmailAddress.objects.get(user=h.user).verified)

		self.assertEqual(count_emails(), 1)

		response = self.healer_confirm(h.user)
		self.assertEqual(response.status_code, 200)
		h = Healer.objects.get(id=h.id)
		self.assertFalse(User.objects.filter(id=dummy_user.id).count())
		self.assertTrue(EmailAddress.objects.get(user=h.user).verified)
		self.assertTrue(h.user.is_active)

	def test_wellness_center_not_ambassador(self):
		self.wc.ambassador_plan = None
		self.wc.save()

		response = self.client.post(reverse('healer_create'), self.provider_data)
		self.assertEqual(response.status_code, 302)

		h = Healer.objects.get(user__email=self.provider_data['email'])
		self.assertFalse(h.ambassador)
		self.assertFalse(h.ambassador_plan)

	def test_wellness_center_ambassador(self):
		response = self.client.post(reverse('healer_create'), self.provider_data)
		self.assertEqual(response.status_code, 302)

		h = Healer.objects.get(user__email=self.provider_data['email'])
		self.assertEqual(h.ambassador.user, self.wc.user)
		self.assertEqual(h.ambassador_plan, self.wc.ambassador_plan)


class WcentersEditProviderProfileTest(WcentersBaseTest):
	def setUp(self):
		def add_location():
			l = Location(title='test',
				addressVisibility=Healer.VISIBLE_EVERYONE,
				address_line1='test',
				address_line2='test',
				postal_code='test',
				city='test',
				state_province='test',
				country='test',
				color=LOCATION_COLOR_LIST[1])
			l.save()
			ClientLocation(client=self.wc, location=l).save()

		super(WcentersEditProviderProfileTest, self).setUp()
		add_location()

		Referrals.objects.create(to_user=self.test_healer.user, from_user=self.wc.user)
		self.test_healer.wellness_center_permissions.add(self.wc)

	def test_not_wellness_center(self):
		h = Healer.objects.get(id=4)
		h.user.set_password('test')
		h.user.save()
		result_login = self.client.login(email=h.user.email, password='test')
		self.assertTrue(result_login)
		response = self.client.get(reverse('healer_edit', args=[self.test_healer.user.username]))
		self.assertEqual(response.status_code, 404)

	def test_not_friends(self):
		Referrals.objects.filter(to_user=self.test_healer.user).delete()
		response = self.client.get(reverse('healer_edit', args=[self.test_healer.user.username]))
		self.assertEqual(response.status_code, 404)

	def test_photo_edit_view_form(self):
		response = self.client.get(reverse('avatar_change', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['primary_avatar_form']), PrimaryAvatarForm)

	def test_email_edit_view_form(self):
		response = self.client.get(reverse('edit_email', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['edit_user'], self.test_healer.user)

	def test_healer_edit_view_form(self):
		response = self.client.get(reverse('healer_edit', args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), HealerForm)

	def test_healer_edit_view_post(self):
		data = {'first_name': 'first name', 'last_name': 'last name',
				'about': '<div style="color: red;">test</div>',
				'profileVisibility': 2,
				'timezone': Timezone.TIMEZONE_CHOICES[0][0],
				'client_screening': 2,
				'ghp_notification_frequency': 'every time'}
		self.client.post(reverse('healer_edit', args=[self.test_healer.user.username]), data)

		healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(healer.user.first_name, 'first name')
		self.assertEqual(healer.user.last_name, 'last name')
		self.assertEqual(healer.about, '<div style="">\n   test\n  </div>')
		self.assertEqual(healer.profileVisibility, 2)
		self.assertEqual(healer.beta_tester, True)
		self.assertEqual(healer.client_screening, 2)
