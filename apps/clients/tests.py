from datetime import datetime, timedelta

from django import test
from django.conf import settings
from django.core.urlresolvers import reverse

from friends.models import Friendship
from emailconfirmation.models import EmailAddress, EmailConfirmation

from contacts_hs.models import ContactInfo
from healers.models import (Appointment, Healer, Clients, get_minutes,
	TreatmentTypeLength)
from healers.tests import create_test_time
from clients.models import Client, SiteJoinInvitation
from util import get_email

settings.GET_NOW = create_test_time


class ClientsTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'treatments.json']

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_client = Client.objects.get(pk=5)
		self.test_client.user.set_password('test')
		self.test_client.user.save()

		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		self.treatment_length = TreatmentTypeLength.objects.all()[0]

	def create_appointment(self, **kwargs):
		kwargs['created_by'] = kwargs['healer'].user
		kwargs['created_date'] = settings.GET_NOW()
		kwargs['last_modified_by'] = kwargs['healer'].user
		kwargs['last_modified_date'] = settings.GET_NOW()
		return Appointment.objects.create(**kwargs)


class ClientDetailTest(ClientsTest):
	def setUp(self):
		""" Invitation from healer to client, clients friendship, dummy users exists """

		self.test_healer = Healer.objects.get(pk=1)
		self.test_client = Client.objects.get(pk=5)
		self.client_info = ContactInfo.objects.create(client=self.test_client, healer=self.test_healer)

		self.test_healer.user.set_password('test')
		self.test_healer.user.save()

		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)

	def test_not_my_client(self):
		response = self.client.get(reverse('client_detail', args=[self.test_client.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['client_info'], None)

	def test_my_client(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		response = self.client.get(reverse('client_detail', args=[self.test_client.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['client_info'],
			self.test_client.contact_info(separator='<br />', email_link=True))


class AppointsmentsTest(ClientsTest):
	def test_appointments_view_correct_response(self):
		response = self.client.get(reverse('receiving_appointments'))

		self.assertEqual(response.status_code, 200)

	def test_appointment_cancel_view_wrong_id(self):
		response = self.client.get(reverse('appointment_cancel', args=[0]))

		self.assertEqual(response.status_code, 404)

	def test_appointment_cancel_view_not_access(self):
		start = create_test_time()
		end = start + timedelta(hours=1)
		appointment = self.create_appointment(healer=Healer.objects.get(pk=1),
			client=Client.objects.get(pk=3),
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=None,
			treatment_length=self.treatment_length)

		response = self.client.get(reverse('appointment_cancel', args=[appointment.id]))
		self.assertContains(response, 'Allowed', status_code=404)

	def test_appointment_cancel_view_success(self):
		start = create_test_time()
		end = start + timedelta(hours=1)
		appointment = self.create_appointment(healer=Healer.objects.get(pk=1),
			client=self.test_client,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=None,
			treatment_length=self.treatment_length)

		response = self.client.get(reverse('appointment_cancel', args=[appointment.id]))
		self.assertEqual(response.status_code, 302)
		self.assertTrue(Appointment.canceled_objects.get(pk=appointment.id).canceled)
		self.assertFalse(Appointment.objects.filter(pk=appointment.id).count())

		email = get_email()
		self.assertNotEqual(email.subject.find('canceled'), -1)
		self.assertNotEqual(email.body.find('canceled'), -1)


class ProfileTest(ClientsTest):
	def test_profile_edit_view_correct_response(self):
		response = self.client.get(reverse('clients_profile'))

		self.assertEqual(response.status_code, 200)

	def test_profile_edit_view_post(self):
		data = {'first_name': 'first name', 'last_name': 'last name',
				'about': 'test', 'ghp_notification_frequency': 'every time'}
		self.client.post(reverse('clients_profile'), data)
		client = Client.objects.get(pk=self.test_client.pk)
		self.assertEqual(client.user.first_name, data['first_name'])
		self.assertEqual(client.user.last_name, data['last_name'])
		self.assertEqual(client.about, data['about'])  # '<p>\n   test\n  </p>')

	#		self.assertEqual(client.beta_tester, True)

	def test_client_view_correct_response(self):
		response = self.client.get(reverse('client_public_profile', args=[self.test_client.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.test_client.user.client)

	def test_client_public_profile_view_correct_response(self):
		response = self.client.get(reverse('client_public_profile', args=[self.test_client.user.username]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.test_client.user.client)

	def test_email_view_correct_response(self):
		response = self.client.get(reverse('edit_email'))

		self.assertEqual(response.status_code, 200)


class HealersTest(ClientsTest):
	def test_healers_friends_view_correct_response(self):
		response = self.client.get(reverse('friends', args=['healers']))

		self.assertEqual(response.status_code, 200)


class DisableRemindersViewTest(ClientsTest):

	def test_disable(self):
		self.test_client.send_reminders = True
		self.test_client.save()

		response = self.client.get(reverse('disable_reminders'))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Client.objects.get(id=self.test_client.id).send_reminders)


class EmailConfirmationViewTest(ClientsTest):

	def setUp(self):
		self.test_client = Client.objects.get(pk=5)
		self.test_healer = Healer.objects.get(pk=1)

	def test_invalid_key(self):
		response = self.client.get(reverse('emailconfirmation_confirm_email', args=['123']))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Invalid confirmation key')

	def test_next_redirect(self):
		email_address = EmailAddress.objects.create(user=self.test_client.user,
			email=self.test_client.user.email)
		EmailConfirmation.objects.create(
			email_address=email_address,
			confirmation_key='123',
			sent=datetime.now())
		response = self.client.get(
			reverse('emailconfirmation_confirm_email',
					args=['123']) + '?next=/search/')

		self.assertRedirects(response, '/search/', 302)

	def test_client_redirect(self):
		email_address = EmailAddress.objects.create(user=self.test_client.user, email=self.test_client.user.email)
		EmailConfirmation.objects.create(
			email_address=email_address,
			confirmation_key='123',
			sent=datetime.now())
		response = self.client.get(reverse('emailconfirmation_confirm_email', args=['123']))
		self.assertRedirects(response, reverse('what_next'), 302, 302)

	def test_healer_redirect(self):
		email_address = EmailAddress.objects.create(user=self.test_healer.user, email=self.test_healer.user.email)
		EmailConfirmation.objects.create(
			email_address=email_address,
			confirmation_key='123',
			sent=datetime.now())
		response = self.client.get(reverse('emailconfirmation_confirm_email', args=['123']))

		self.assertRedirects(response, reverse('what_next'), 302, 302)

	def test_friendship_exists(self):
		SiteJoinInvitation.objects.send_invitation(self.test_healer.user, self.test_client.user.email)
		Friendship.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		email_address = EmailAddress.objects.create(user=self.test_client.user, email=self.test_client.user.email)
		EmailConfirmation.objects.create(
			email_address=email_address,
			confirmation_key='123',
			sent=datetime.now())

		self.client.get(reverse('emailconfirmation_confirm_email', args=['123']))

		self.assertEqual(Friendship.objects.filter(from_user=self.test_healer.user, to_user=self.test_client.user).count(), 1)

import urllib
import json
from rest_framework.test import APIClient


class UpdateProfileAjaxBaseTest(ClientsTest):
	def setUp(self):
		super(UpdateProfileAjaxBaseTest, self).setUp()
		self.data = {
			'email': self.test_client.user.email,
			'password': 'test',
			'first_name': 'First Last',
			'about': 'Test',
			'location': 'La Ciotat, France'
		}
		self.point = {
			'lat': 43.17365299999999,
			'lng': 5.605155
		}
		self.rest_client = APIClient()

	def post(self):
		response = self.rest_client.post(
			reverse('update_profile_ajax'),
			self.data)
		return json.loads(response.content)


class UpdateProfileAjaxTest(UpdateProfileAjaxBaseTest):

	def test_success(self):
		response = self.post()
		self.assertFalse('errors' in response)
		self.assertFalse('detail' in response)
		client = Client.objects.get(id=self.test_client.id)
		self.assertEqual(client.user.first_name, 'First')
		self.assertEqual(client.user.last_name, 'Last')
		self.assertEqual(client.about, 'Test')
		locations = client.get_locations_objects()
		self.assertTrue(locations)
		self.assertEqual(locations[0].point.x, self.point['lng'])
		self.assertEqual(locations[0].point.y, self.point['lat'])

	def test_wrong_credentials(self):
		self.data['password'] = ''
		response = self.post()
		self.assertTrue(response['detail'], 'Not found')

	def test_no_first_name(self):
		self.data['first_name'] = ''
		response = self.post()
		self.assertTrue('errors' in response)


class UpdateProfileAjaxAuthenticatedTest(UpdateProfileAjaxBaseTest):

	def setUp(self):
		super(UpdateProfileAjaxAuthenticatedTest, self).setUp()
		del self.data['email']
		del self.data['password']
		self.rest_client.force_authenticate(user=self.test_client.user)

	def test_success(self):
		response = self.post()
		self.assertFalse('errors' in response)
		self.assertFalse('detail' in response)

