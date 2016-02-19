# -*- coding: utf-8 -*-

import Cookie
import json
import time
import urllib
from datetime import timedelta
from captcha import conf
from captcha.models import CaptchaStore

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpRequest

from friends.models import Contact, Friendship
from oauth_access.access import OAuthAccess
from django_dynamic_fixture import G
from rest_framework.test import APIClient
from emailconfirmation.models import EmailAddress, EmailConfirmation

from sync_hs.facebook import FacebookCallback
from ambassador.settings import COOKIE_NAME as AMBASSADOR_COOKIE_NAME
from ambassador.models import Plan
from contacts_hs.models import ContactEmail, ContactInfo

from clients.models import (Client, SiteJoinInvitation, ClientPhoneNumber,
	ClientLocation)
from clients.tests import ClientsTest
from healers.models import (Healer, HealerTimeslot, get_minutes, ClientInvitation,
	is_healer, Appointment, WellnessCenter, Referrals, Clients, TreatmentTypeLength,
	Location)

from healers.tests import HealersTest, create_test_time, get_email, count_emails


class SignupViewBaseTest(ClientsTest):
	def setUp(self, client=False):
		def get_invitation_user():
			if client:
				return self.test_client.user
			else:
				return self.test_healer.user

		self.test_healer = Healer.objects.get(pk=1)
		if not client:
			self.test_client = Client.objects.get(pk=1)

		self.email = 'test@healersource.com'
		self.confirmation_key = '123'
		self.contact, created = Contact.objects.get_or_create(email=self.email, user=self.test_client.user)
		self.create_invitation(get_invitation_user())

	def create_invitation(self, user):
		self.invitation = SiteJoinInvitation.objects.create(from_user=user,
			contact=self.contact,
			message="",
			status="2",
			confirmation_key=self.confirmation_key)


class SignupViewTest(SignupViewBaseTest):
	def test_logined_message(self):
		self.test_client.user.set_password('test')
		self.test_client.user.save()
		result_login = self.client.login(email=self.test_client.user.email, password='test')
		self.assertTrue(result_login)

		response = self.client.get(reverse('signup'))

		self.assertContains(response, 'logged in')


class SignupAjaxBaseTest(SignupViewBaseTest):
	def setUp(self, **kwargs):
		super(SignupAjaxBaseTest, self).setUp(**kwargs)
		self.data = {
			# 'is_ambassador': 0, # put in when phonegap backward compatibility is removed
			'email': self.email,
			'password1': 'test1234',
			'password2': 'test1234',
			'first_name': 'test'}
		self.rest_client = APIClient()

	def signup(self, type='client', confirm=False, cookies=None):
		if cookies is not None:
			self.rest_client.cookies = Cookie.SimpleCookie(cookies)
		self.data['type'] = type
		if confirm:
			self.data['confirmation_key'] = self.confirmation_key
		response = self.rest_client.post(reverse('ajax_signup'),
			{'data': urllib.urlencode(self.data),
			'is_phonegap': json.dumps(False)})
		return json.loads(response.content)


class ProccessDummyUsersTest(SignupAjaxBaseTest):
	def setUp(self):
		""" Invitation from healer to client, clients friendship, dummy users exists """

		self.test_client = Client.objects.get(pk=3)
		super(ProccessDummyUsersTest, self).setUp(client=self.test_client)

		self.test_healer2 = Healer.objects.get(pk=4)

		self.treatment_length = TreatmentTypeLength.objects.all()[0]

		# create dummy clients with appointment and invitation
		timestamp = str(time.time())
		self.dummy_user1 = User(username=timestamp, first_name='Test', last_name='Test', email=self.email,
			is_active=False)
		self.dummy_user1.set_unusable_password()
		self.dummy_user1.save()
		self.dummy_user2 = User(username=timestamp + '1', first_name='Test', last_name='Test', email=self.email,
			is_active=False)
		self.dummy_user2.set_unusable_password()
		self.dummy_user2.save()

		start = create_test_time()
		end = start + timedelta(hours=2)

		client1 = Client.objects.get_or_create(user=self.dummy_user1)[0]
		client1.referred_by = 'test healer'
		client1.save()
		ClientPhoneNumber.objects.create(client=client1, number='2223322')
		ClientLocation.objects.create(client=client1, location=Location.objects.create(title='test'))
		ClientLocation.objects.create(client=client1, location=Location.objects.create(title='test1'))
		client2 = Client.objects.get_or_create(user=self.dummy_user2)[0]
		self.appointment1 = self.create_appointment(healer=self.test_healer,
			client=client1,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			confirmed=False,
			treatment_length=self.treatment_length)
		self.appointment2 = self.create_appointment(healer=self.test_healer,
			client=client2,
			start_date=start.date() + timedelta(days=1),
			end_date=end.date() + timedelta(days=1),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			confirmed=False,
			treatment_length=self.treatment_length)
		self.appointment3 = self.create_appointment(healer=self.test_healer2,
			client=client2,
			start_date=start.date() + timedelta(days=2),
			end_date=end.date() + timedelta(days=2),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			confirmed=False,
			treatment_length=self.treatment_length)
		self.conflict_appointment = self.create_appointment(healer=self.test_healer,
			client=Client.objects.get(pk=5),
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start) + 60,
			end_time=get_minutes(end),
			confirmed=False,
			treatment_length=self.treatment_length)
		self.timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end),
			location=None)

	def test_unicode_name(self):
		self.data['first_name'] = u'тест'.encode('utf-8')
		self.signup()
		self.assertEqual(u'тест', User.objects.filter(email=self.email)[2].first_name)

	def test_not_verified_email(self):
		SiteJoinInvitation.objects.all().delete()

		self.signup()

		dummy_users = User.objects.filter(id__in=[self.dummy_user1.id, self.dummy_user2.id])
		self.assertEqual(dummy_users.count(), 2)

		confirmation_key = EmailConfirmation.objects.get(email_address__email=self.email).confirmation_key
		EmailConfirmation.objects.confirm_email(confirmation_key)

		dummy_users = User.objects.filter(id__in=[self.dummy_user1.id, self.dummy_user2.id])
		self.assertEqual(dummy_users.count(), 0)

	def test_verified_email(self):
		self.signup(confirm=True)

		dummy_users = User.objects.filter(id__in=[self.dummy_user1.id, self.dummy_user2.id])
		self.assertEqual(dummy_users.count(), 0)

	def test_client_fields_copy(self):
		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)
		friendship = Clients.objects.filter(from_user=self.test_client.user,
			to_user=new_user).count()
		self.assertEqual(friendship, 1)

		client = Client.objects.get(user=new_user)

		self.assertEqual(client.referred_by, 'test healer')
		self.assertEqual(client.phone_numbers.all()[0].number, '2223322')
		self.assertEqual(self.contact.users.filter(id=new_user.id).count(), 1)

		locations = [cl.location.title for cl in client.clientlocation_set.all()]
		self.assertTrue('test' in locations)
		self.assertTrue('test1' in locations)

	def test_healer_auto_confirm(self):
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_AUTO
		self.test_healer.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)
		friendship = Clients.objects.filter(from_user=self.test_client.user,
			to_user=new_user).count()
		self.assertEqual(friendship, 1)

		# check dummy user removed
		users = User.objects.filter(email=self.email)
		self.assertEqual(users.count(), 1)

		# check that appointments updated to new client and confirmed
		appointment1 = Appointment.objects.get(pk=self.appointment1.pk)
		self.assertEqual(users[0].pk, appointment1.client.user.pk)
		self.assertTrue(appointment1.confirmed)

		appointment2 = Appointment.objects.get(pk=self.appointment2.pk)
		self.assertEqual(users[0].pk, appointment2.client.user.pk)
		self.assertTrue(appointment2.confirmed)

		appointment3 = Appointment.objects.get(pk=self.appointment2.pk)
		self.assertEqual(users[0].pk, appointment3.client.user.pk)
		self.assertTrue(appointment3.confirmed)

		# check emails
		email = get_email()
		self.assertNotEqual(email.subject.find('confirmed'), -1)  # appt1

		email = get_email(1)
		self.assertIn('declined', email.subject)  # conflict_appt

		email = get_email(2)
		self.assertNotEqual(email.subject.find('created'), -1)  # appt1

		email = get_email(3)
		self.assertNotEqual(email.subject.find('confirmed'), -1)  # appt2

		email = get_email(4)
		self.assertNotEqual(email.subject.find('created'), -1)  # appt2

		# check that conflict appointment and healer timeslot removed
		self.assertFalse(Appointment.objects.filter(pk=self.conflict_appointment.pk).count())

	def test_healer_manual_new_confirm_client(self):
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL_NEW
		self.test_healer.save()
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.dummy_user2)

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)
		friendship = Clients.objects.filter(from_user=self.test_client.user,
			to_user=new_user).count()
		self.assertEqual(friendship, 1)

		# check dummy user removed
		users = User.objects.filter(email=self.email)
		self.assertEqual(users.count(), 1)

		# check that appointments updated to new client and confirmed
		appointment1 = Appointment.objects.get(pk=self.appointment1.pk)
		self.assertEqual(users[0].pk, appointment1.client.user.pk)
		self.assertTrue(appointment1.confirmed)

		appointment2 = Appointment.objects.get(pk=self.appointment2.pk)
		self.assertEqual(users[0].pk, appointment2.client.user.pk)
		self.assertTrue(appointment2.confirmed)

		# check that conflict appointment and healer timeslot removed
		self.assertFalse(Appointment.objects.filter(pk=self.conflict_appointment.pk).count())

	def test_healer_manual_new_confirm(self):
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL_NEW
		self.test_healer.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)
		friendship = Clients.objects.filter(from_user=self.test_client.user,
			to_user=new_user).count()
		self.assertEqual(friendship, 1)

		# check dummy user removed
		users = User.objects.filter(email=self.email)
		self.assertEqual(users.count(), 1)

		# check that appointments updated to new client and not confirmed
		appointment1 = Appointment.objects.get(pk=self.appointment1.pk)
		self.assertEqual(users[0].pk, appointment1.client.user.pk)
		self.assertFalse(appointment1.confirmed)

		appointment2 = Appointment.objects.get(pk=self.appointment2.pk)
		self.assertEqual(users[0].pk, appointment2.client.user.pk)
		self.assertFalse(appointment2.confirmed)

		# check emails
		email = get_email()
		self.assertNotEqual(email.subject.find('requested'), -1)  # appt1

		email = get_email(1)
		self.assertNotEqual(email.subject.find('requested'), -1)  # appt2

		# check that conflict appointment and healer timeslot not removed
		self.assertTrue(Appointment.objects.filter(pk=self.conflict_appointment.pk).count())
		self.assertTrue(HealerTimeslot.objects.filter(pk=self.timeslot.pk).count())

	def test_healer_manual_confirm(self):
		self.test_healer.manualAppointmentConfirmation = Healer.CONFIRM_MANUAL
		self.test_healer.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)
		friendship = Clients.objects.filter(from_user=self.test_client.user,
			to_user=new_user).count()
		self.assertEqual(friendship, 1)

		# check dummy user removed
		users = User.objects.filter(email=self.email)
		self.assertEqual(users.count(), 1)

		# check that appointments updated to new client and not confirmed
		appointment1 = Appointment.objects.get(pk=self.appointment1.pk)
		self.assertEqual(users[0].pk, appointment1.client.user.pk)
		self.assertFalse(appointment1.confirmed)

		appointment2 = Appointment.objects.get(pk=self.appointment2.pk)
		self.assertEqual(users[0].pk, appointment2.client.user.pk)
		self.assertFalse(appointment2.confirmed)

		# check that conflict appointment and healer timeslot not removed
		self.assertTrue(Appointment.objects.filter(pk=self.conflict_appointment.pk).count())
		self.assertTrue(HealerTimeslot.objects.filter(pk=self.timeslot.pk).count())

	def test_healer_friendship_screen_none(self):
		self.test_healer2.client_screening = Healer.SCREEN_NONE
		self.test_healer2.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)

		friendship = Clients.objects.filter(from_user=self.test_healer2.user, to_user=new_user).count()
		self.assertEqual(friendship, 1)

		invitation = ClientInvitation.objects.filter(from_user=new_user, to_user=self.test_healer2.user, status="2").count()
		self.assertEqual(invitation, 0)

	def test_healer_friendship_screen_all(self):
		self.test_healer2.client_screening = Healer.SCREEN_ALL
		self.test_healer2.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)

		friendship = Clients.objects.filter(from_user=self.test_healer2.user, to_user=new_user).count()
		self.assertEqual(friendship, 0)

		invitation = ClientInvitation.objects.filter(from_user=new_user, to_user=self.test_healer2.user, status="2").count()
		self.assertEqual(invitation, 1)

	def test_healer_friendship_screen_not_contacts(self):
		self.test_healer2.client_screening = Healer.SCREEN_NOT_CONTACTS
		self.test_healer2.save()
		ContactEmail.objects.create(email=self.contact.email, contact=ContactInfo.objects.create(healer=self.test_healer2))

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_user = User.objects.get(email=self.email)

		friendship = Clients.objects.filter(from_user=self.test_healer2.user, to_user=new_user).count()
		self.assertEqual(friendship, 1)

		invitation = ClientInvitation.objects.filter(from_user=new_user, to_user=self.test_healer2.user, status="2").count()
		self.assertEqual(invitation, 0)


class SignupAccessTest(SignupAjaxBaseTest):
	def test_healer_not_confirmed(self):
		"""Only setup should be available for healers without confirmed emails on signup."""
		self.signup('healer')

		response = self.rest_client.get(reverse('provider_setup_intro'))
		self.assertEqual(response.status_code, 200)

		# check if any other page except setup is available
		response = self.rest_client.get(reverse('notes'))
		self.assertEqual(response.status_code, 302)

	def test_client_not_confirmed(self):
		"""Clients should not login on signup if email is not confirmed."""
		self.signup()

		response = self.rest_client.get(reverse('provider_setup_intro'))
		self.assertEqual(response.status_code, 302)


class SignupRedirectTest(SignupAjaxBaseTest):
	def test_client_redirect(self):
		response = self.signup(confirm=True)
		url = response['redirect_url']
		self.assertEqual(url, reverse('what_next'))

		response = self.rest_client.get(url)
		self.assertRedirects(response, reverse('friends', args=['healers']), 302)

	def test_healer_redirect(self):
		response = self.signup('healer', True)
		url = response['redirect_url']
		self.assertEqual(url, reverse('what_next'))

		response = self.rest_client.get(url)
		self.assertRedirects(response, reverse('provider_setup', args=[0]), 302)


class SignupUsernameTest(SignupAjaxBaseTest):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'treatments.json', 'modality.json']

	def test_url_exists(self):
		username_url = reverse('privacy').strip('/')
		self.data.update({'first_name': username_url})

		self.signup('healer', True)
		self.assertEqual(Client.objects.filter(user__username__iexact=username_url).count(), 0)
		self.assertEqual(Healer.objects.filter(user__username__iexact=username_url).count(), 0)
		self.assertEqual(Healer.objects.filter(user__username='{0}1'.format(username_url)).count(), 1)

	def test_username_exists(self):
		self.data.update({'first_name': self.test_client.user.username})
		self.signup('healer', True)
		self.assertEqual(Client.objects.filter(user__username__iexact=self.test_client.user.username).count(), 1)
		self.assertEqual(Healer.objects.filter(user__username__iexact='{0}1'.format(self.test_client.user.username)).count(), 1)

	def test_username_not_real_for_client(self):
		self.data.update({'first_name': 'First Last'})
		self.signup(confirm=True)
		self.assertEqual(Client.objects.filter(user__username__iexact='first_last').count(), 0)

	def test_success_for_healer(self):
		self.data.update({'first_name': 'First Last'})
		response = self.signup('healer', True)
		self.assertTrue('redirect_url' in response)
		self.assertEqual(Healer.objects.filter(user__username__iexact='first_last').count(), 1)

	def test_success_for_healer_only_first_name(self):
		self.data.update({'first_name': 'Firstoo'})
		self.signup('healer', True)
		self.assertEqual(Healer.objects.filter(user__username__iexact='firstoo').count(), 1)

	def test_username_too_short(self):
		self.data.update({'first_name': 'fir'})
		self.signup('healer', True)
		self.assertEqual(Healer.objects.filter(user__username__iexact=self.email.replace('@', '_at_').replace('.', '_')).count(), 1)

	def test_username_numbered_exists(self):
		self.data.update({'first_name': 'Firstoo1'})
		self.signup('healer', True)
		self.create_invitation(self.test_healer.user)
		self.data.update({'first_name': 'Firstoo1'})
		self.signup('healer', True)
		self.assertEqual(Healer.objects.filter(user__username__iexact='firstoo2').count(), 1)

	def test_email_too_long(self):
		self.email = 'email'*6 + '@healersource.com'
		self.data['email'] = self.email
		self.signup('healer')
		self.assertEqual(Healer.objects.filter(user__username=self.email[:settings.USERNAME_MAX_LENGTH]).count(), 1)

	def test_modality_exists(self):
		self.data['first_name'] = 'Yoga1'
		self.signup('healer')
		self.assertEqual(Healer.objects.filter(user__username__iexact=self.data['first_name']).count(), 0)

	def test_modality_category_exists(self):
		self.data['first_name'] = 'Massage'
		self.signup('healer')
		self.assertEqual(Healer.objects.filter(user__username__iexact=self.data['first_name']).count(), 0)


class SignupTrackingTest(SignupAjaxBaseTest):
	def fb_tracking(self, type=None, code=None):
		def contains_fb_tracking(content):
			self.assertIn("window._fbq.push(['track', '{}'".format(code), content)
			self.assertIn('src="https://www.facebook.com/tr?ev={}'.format(code), content)

		response = self.signup(type=type)
		url = response['url']
		self.assertEqual(url, reverse('signup_thanks', args=[type]))

		response = self.rest_client.get(url)
		if code is None:
			code = settings.TRACKING_CODES[type]['fb']
		contains_fb_tracking(response.content)

	def test_fb_tracking_client(self):
		self.fb_tracking('client')

	def test_fb_tracking_healer(self):
		self.fb_tracking('healer')

	def test_notes_landing_tracking(self):
		self.rest_client.get(reverse('landing_page_notes'))
		self.fb_tracking('client', settings.TRACKING_CODES['notes_landing']['fb'])

	def test_notes_landing_right_tracking(self):
		self.rest_client.get(reverse('landing_page_notes'), {'fb_signup_code': '888'})
		self.fb_tracking('client', '888')


class SignupTest(SignupAjaxBaseTest):
	def test_form_post_email_not_verified(self):
		response = self.signup()
		self.assertEqual(response['email'], self.email)
		self.assertEqual(User.objects.get(email=self.email).is_active, False)

	def test_invitation_after_signup(self):
		self.test_healer.client_screening = Healer.SCREEN_NONE
		self.test_healer.save()

		self.signup()
		user = User.objects.get(email=self.email)
		self.assertEqual(user.is_active, False)
		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=user).count()
		self.assertEqual(clients, 0)

		self.signup(confirm=True)

		self.assertEqual(User.objects.filter(email=self.email).count(), 1)
		user = User.objects.get(email=self.email)
		self.assertEqual(user.is_active, True)
		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=user).count()
		self.assertEqual(clients, 1)

	def test_invitation_user_is_active(self):
		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)
		self.assertEqual(User.objects.get(email=self.email).is_active, True)

	def test_wellness_center(self):
		response = self.signup('wellness_center')
		self.assertEqual(response['email'], self.email)
		self.assertEqual(WellnessCenter.objects.filter(user__email=self.email).count(), 1)

	def test_healer_error_long_first_name(self):
		self.data['first_name'] = self.data['first_name']*10
		response = self.signup('healer')
		self.assertEqual(Healer.objects.filter(user__email=self.email).count(), 0)
		self.assertTrue('first_name' in response['error_elements'])

	def test_client_error_empty_name(self):
		self.data['first_name'] = ''
		response = self.signup('client')
		self.assertEqual(Client.objects.filter(user__email=self.email).count(), 0)
		self.assertTrue('first_name' in response['error_elements'])

	def test_client_allowed_empty_name(self):
		self.data['first_name'] = ''
		self.data['no_name'] = True
		response = self.signup('client')
		self.assertEqual(Client.objects.filter(user__email=self.email).count(), 1)

	def test_passwords_dont_match(self):
		self.data['password1'] = 'passpasspass'
		response = self.signup()
		self.assertEqual(Client.objects.filter(user__email=self.email).count(), 0)
		self.assertTrue('You must type the same password each time' in response['errors'])

	def test_invitation_email_changed(self):
		self.data.update({'email': 'changed_email@healersource.com'})

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)
		self.assertEqual(User.objects.get(first_name='test').email, self.email)

	def check_friendship_clients_refferals_numbers(self, new_healer,
													friendship_count,
													clients_count,
													referrals_count):
		friendship = Friendship.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(friendship, friendship_count)

		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(clients, clients_count)

		referrals = Referrals.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(referrals, referrals_count)

	def test_healer2healer_as_healer(self):
		self.invitation.is_to_healer = True
		self.invitation.save()

		response = self.signup('healer', True)
		self.assertTrue('redirect_url' in response)
		# self.assertRedirects(response, reverse("provider_setup", args=[0]))
		new_healer = Healer.objects.get(user__email=self.email)

		self.check_friendship_clients_refferals_numbers(new_healer, 1, 0, 1)

	def test_healer2healer_as_healer_no_friendship(self):
		self.invitation.is_to_healer = True
		self.invitation.create_friendship = False
		self.invitation.save()

		response = self.signup('healer', True)

		self.assertTrue('redirect_url' in response)

		new_healer = Healer.objects.get(user__email=self.email)
		self.check_friendship_clients_refferals_numbers(new_healer, 0, 0, 0)

	def test_healer2healer_as_client(self):
		self.test_healer.client_screening = Healer.SCREEN_NONE
		self.test_healer.save()

		self.invitation.is_to_healer = True
		self.invitation.save()

		response = self.signup(confirm=True)
		self.assertTrue('redirect_url' in response)

		new_client = Client.objects.get(user__email=self.email)
		self.assertFalse(is_healer(new_client))
		self.check_friendship_clients_refferals_numbers(new_client, 1, 1, 0)

	def test_healer2client_as_healer(self):
		response = self.signup('healer', True)

		self.assertTrue('redirect_url' in response)

		new_healer = Healer.objects.get(user__email=self.email)
		self.check_friendship_clients_refferals_numbers(new_healer, 1, 1, 0)

	def test_healer2client_as_client(self):
		self.test_healer.client_screening = Healer.SCREEN_NONE
		self.test_healer.save()

		response = self.signup(confirm=True)

		self.assertTrue('redirect_url' in response)

		new_client = Client.objects.get(user__email=self.email)
		self.assertFalse(is_healer(new_client))
		self.check_friendship_clients_refferals_numbers(new_client, 1, 1, 0)

		client = Client.objects.get(user__email=self.email)
		self.assertEqual(client.approval_rating, 100)

	def test_form_post_contact_info_update(self):
		contact_info = ContactInfo.objects.create(contact=self.contact, healer=self.test_healer)
		response = self.signup(confirm=True)

		self.assertTrue('redirect_url' in response)

		contact_info = ContactInfo.objects.get(id=contact_info.id)
		self.assertEqual(contact_info.client, Client.objects.get(user__email=self.email))

	def test_dummy_user_as_healer(self):
		user = User.objects.create(email=self.email, username='12344567', is_active=False)
		user.set_unusable_password()
		user.save()
		Client.objects.create(user=user)

		response = self.signup('healer', True)

		self.assertTrue('redirect_url' in response)

		new_healer = Healer.objects.get(user__email=self.email)
		self.check_friendship_clients_refferals_numbers(new_healer, 1, 1, 0)

	def test_inactive_user_duplicate(self):
		SiteJoinInvitation.objects.all().delete()

		self.data = {
			'email': self.email,
			'password1': 'password',
			'password2': 'password',
			'type': 'client',
			'is_ambassador': 0,
			'no_name': 1
		}

		dummy_users = User.objects.filter(email=self.data['email'], is_active=False)
		self.assertEqual(dummy_users.count(), 1)
		self.assertTrue(dummy_users[0].check_password(self.data['password1']))

		dummy_users = User.objects.filter(email=self.data['email'], is_active=False)
		self.assertEqual(dummy_users.count(), 1)
		self.assertTrue(dummy_users[0].check_password(self.data['password1']))


class SignupAmbassadorTest(SignupAjaxBaseTest):
	def test_client_as_ambassador(self):
		self.data['is_ambassador'] = '1'
		response = self.signup()
		self.assertEqual(response['email'], self.email)
		c = Client.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)
		self.assertFalse(is_healer(c[0]))

	def test_healer_as_ambassador(self):
		self.data['is_ambassador'] = '1'
		response = self.signup('healer')
		self.assertEqual(response['email'], self.email)
		c = Healer.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)

	def test_wellness_center_as_ambassador(self):
		self.data['is_ambassador'] = '1'
		response = self.signup('wellness_center')
		self.assertEqual(response['email'], self.email)
		c = WellnessCenter.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)

	def test_set_ambassador_from_invite(self):
		ambassador = Client.objects.get(user__id=self.invitation.from_user.id)
		ambassador.ambassador_plan = G(Plan)
		ambassador.save()

		response = self.signup(confirm=True)
		self.assertEqual(response['redirect_url'], reverse('what_next'))

		new_client = Client.objects.get(user__email=self.email)
		self.assertEqual(new_client.ambassador.user, self.invitation.from_user)
		self.assertEqual(new_client.ambassador_plan, ambassador.ambassador_plan)

	def test_set_ambassador_from_cookie(self):
		ambassador = G(Client)
		self.signup(cookies={
			AMBASSADOR_COOKIE_NAME: ambassador.user.username
		})

		new_client = Client.objects.get(user__email=self.email)
		self.assertEqual(new_client.ambassador.user, ambassador.user)
		self.assertEqual(new_client.ambassador_plan, ambassador.ambassador_plan)


class SignupFacebookTest(SignupViewBaseTest):
	def setUp(self):
		super(SignupFacebookTest, self).setUp()
		self.request = HttpRequest()
		self.request.user = AnonymousUser()
		self.request.session = SessionStore()

	def signup(self, type='client', is_ambassador=False, user_data_changed=None):
		user_data = {'first_name': 'test', 'last_name': 'test', 'email': self.email, 'id': '1'}
		if user_data_changed is not None:
			user_data.update(user_data_changed)
		FacebookCallback().handle_no_user(self.request, OAuthAccess(service='facebook'), user_data, type, is_ambassador)

	def test_username_too_long(self):
		data = {'first_name': 'FirstFirstFirstFi',
			'last_name': 'ZzzzzzzzzZzzzzzzzz'}
		self.signup('healer', user_data_changed=data)

		username = '{0}_{1}'.format(data['first_name'], data['last_name'])
		self.assertEqual(Healer.objects.filter(
			user__username__iexact=username[:settings.USERNAME_MAX_LENGTH]).count(), 1)

	def test_healer2healer_as_healer(self):
		self.invitation.is_to_healer = True
		self.invitation.save()

		self.signup('healer')

		new_healer = Healer.objects.get(user__email=self.email)
		friendship = Friendship.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(friendship, 1)

		refferal = Referrals.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(refferal, 1)

	def test_healer2healer_as_client(self):
		self.test_healer.client_screening = Healer.SCREEN_NONE
		self.test_healer.save()

		self.invitation.is_to_healer = True
		self.invitation.save()

		self.signup()

		new_client = Client.objects.get(user__email=self.email)
		self.assertFalse(is_healer(new_client))

		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=new_client.user).count()
		self.assertEqual(clients, 1)

	def test_healer2client_as_healer(self):
		self.signup('healer')
		new_healer = Healer.objects.get(user__email=self.email)

		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=new_healer.user).count()
		self.assertEqual(clients, 1)

	def test_healer2client_as_client(self):
		self.test_healer.client_screening = Healer.SCREEN_NONE
		self.test_healer.save()

		self.signup()

		new_client = Client.objects.get(user__email=self.email)
		self.assertFalse(is_healer(new_client))

		clients = Clients.objects.filter(from_user=self.test_healer.user,
			to_user=new_client.user).count()
		self.assertEqual(clients, 1)

		client = Client.objects.get(user__email=self.email)
		self.assertEqual(client.approval_rating, 100)

	def test_client_as_ambassador(self):
		self.signup('client', True)

		c = Client.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)
		self.assertFalse(is_healer(c[0]))

	def test_healer_as_ambassador(self):
		self.signup('healer', True)

		c = Healer.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)

	def test_welness_center_as_ambassador(self):
		self.signup('wellness_center', True)

		c = WellnessCenter.objects.filter(user__email=self.email)
		self.assertEqual(c.count(), 1)
		self.assertEqual(c[0].ambassador_program, True)

	def test_set_ambassador_from_cookie(self):
		ambassador = G(Client)
		self.request.COOKIES = {AMBASSADOR_COOKIE_NAME: ambassador.user.username}
		self.signup('wellness_center', True, {})

		new_client = Client.objects.get(user__email=self.email)
		self.assertEqual(new_client.ambassador.user, ambassador.user)
		self.assertEqual(new_client.ambassador_plan, ambassador.ambassador_plan)
		self.assertFalse(AMBASSADOR_COOKIE_NAME in self.request.COOKIES)


class SignupPluginViewTest(ClientsTest):

	def setUp(self):
		self.client.logout()

	def test_plugin(self):
		ambassador = G(Client, ambassador_program=True)
		self.client.cookies = Cookie.SimpleCookie({
			AMBASSADOR_COOKIE_NAME: ambassador.user.username
		})
		response = self.client.get(reverse('signup_plugin'))

		self.assertEqual(response.status_code, 200)

		embed = response.context['embed']
		self.assertEqual(embed['username'], ambassador.user.username)
		self.assertEqual(embed['background_color'], ambassador.embed_background_color)

	def test_plugin_no_cookie(self):
		response = self.client.get(reverse('signup_plugin'))

		self.assertEqual(response.status_code, 404)

	def test_plugin_no_ambassador_program(self):
		ambassador = G(Client, ambassador_program=False)
		self.client.cookies = Cookie.SimpleCookie({
			AMBASSADOR_COOKIE_NAME: ambassador.user.username
		})
		response = self.client.get(reverse('signup_plugin'))

		self.assertEqual(response.status_code, 404)


class SignupClientTest(HealersTest):
	def setUp(self):
		super(SignupClientTest, self).setUp()
		self.rest_client = APIClient()

		challenge, response = conf.settings.get_challenge()()
		store = CaptchaStore.objects.create(challenge=challenge, response=response)
		start = create_test_time() + timedelta(days=2)
		end = start + timedelta(hours=2)

		self.timeslot = HealerTimeslot.objects.create(healer=self.test_healer,
			start_date=start.date(),
			end_date=end.date(),
			start_time=get_minutes(start),
			end_time=get_minutes(end))

		self.data = {'first_name': 'first name',
				'last_name': 'last name',
				'email': 'test@healersource.com',
				'phone': '222-33-22',
				'note': 'test',
				'password1': '11111111',
				'password2': '11111111',
				'security_verification_0': store.hashkey,
				'security_verification_1': store.response,
				'start': 0,
				'timeslot': self.timeslot.id}

	def test_empty_email_fail(self):
		self.data['email'] = ''
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual(json.loads(response.content)['error'], 'email: <ul class="errorlist"><li>This field is required.</li></ul>')

	def test_empty_phone_fail(self):
		self.data['phone'] = ''
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual(json.loads(response.content)['error'], 'phone: <ul class="errorlist"><li>This field is required.</li></ul>')

	def test_invalid_timeslot_fail(self):
		self.data['timeslot'] = 'test'
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual(json.loads(response.content)['error'], 'Timeslot id in invalid format.')

	def test_not_find_timeslot(self):
		self.timeslot.delete()
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual(json.loads(response.content)['error'], 'Could not find that timeslot.')

	def test_captcha(self):
		self.data['security_verification_0'] = 'test'
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertIn('Invalid CAPTCHA', json.loads(response.content)['error'])

		# img = [cmd for cmd in response if cmd.get('id','')=='img.captcha'][0]['val']
		# c0 = [cmd for cmd in response if cmd.get('id','')=='#id_security_verification_0'][0]['val']
		# c1 = [cmd for cmd in response if cmd.get('id','')=='#id_security_verification_1'][0]['val']
		# self.assertTrue(c0 in img)
		# self.assertNotEqual(c0, self.store.hashkey)
		# self.assertFalse(c1)

	def test_registered_user_exist(self):
		u = User.objects.create(username='test', email='test@healersource.com')
		u.set_password('111')
		u.save()
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertIn('Another user is already registered with this email address.', json.loads(response.content)['error'])

	def test_user_exist_unconfirmed_email(self):
		u = User.objects.create(username='test', email='test@healersource.com', is_active=False)
		u.set_unusable_password()
		u.save()
		EmailAddress.objects.add_email(u, u.email)
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual('This email is already in use. Please check your email and click the Email Confirmation link.', json.loads(response.content)['error'])

		email = get_email()
		self.assertNotEqual(email.body.find('confirm your email address'), -1)

	def test_user_exist_no_email_address(self):
		u = User.objects.create(username='test', email='test@healersource.com', is_active=False)
		u.set_unusable_password()
		u.save()
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		self.assertEqual('This email is already in use. Please check your email and click the Email Confirmation link.', json.loads(response.content)['error'])

		email = get_email()
		self.assertNotEqual(email.body.find('confirm your email address'), -1)

	def test_success(self):
		response = self.rest_client.post(reverse('ajax_signup_client'), {'data': urllib.urlencode(self.data)})
		client_pk = response.content
		self.assertEqual(client_pk, '6')

		email2 = get_email()
		self.assertNotEqual(email2.subject.find('Confirm your email address'), -1)
		self.assertNotEqual(email2.body.find('confirm your email address'), -1)

		self.assertEqual(count_emails(), 1)

		user = Client.objects.get(pk=client_pk).user
		self.assertTrue(user.has_usable_password())
		self.assertFalse(user.is_active)


class LoginTest(HealersTest):
	def setUp(self):
		super(LoginTest, self).setUp()
		self.rest_client = APIClient()
		self.data = {
				'email': 'frank@healersource.com',
				'password': 'test'}

	def login(self):
		response = self.rest_client.post(reverse('ajax_login'), {'data': urllib.urlencode(self.data)})
		return json.loads(response.content)

	def test_empty_email_fail(self):
		self.data['email'] = ''
		self.assertEqual(self.login(), 'The following fields have errors: <ul><li>email</li></ul>')

	def test_wrong_login_data(self):
		self.data['email'] = 'test@test.com'
		self.assertIn('The email address and/or password you specified are not correct.', self.login())

	def test_success(self):
		self.assertEqual(self.login(), 1)

	def test_empty_password(self):
		self.data['password'] = ''
		self.assertEqual(self.login(), 'The following fields have errors: <ul><li>password</li></ul>')
