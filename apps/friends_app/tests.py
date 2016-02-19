import urllib
import json

from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.template.defaultfilters import title
from django.contrib.gis.geos import Point
from django_dynamic_fixture import G

from rest_framework.test import APIClient
from emailconfirmation.models import EmailAddress
from avatar.models import Avatar
from friends.models import Contact
from account_hs.forms import ClientSignupForm
from clients.models import Client, SiteJoinInvitation, ClientLocation
from healers.models import Healer, Referrals, Clients, Zipcode, Location
from util import get_email, count_emails
from friends_app.recommendations import ProviderRecommendationsFinder
from friends_app.forms import JoinInviteRequestForm, ContactsJoinInviteRequestForm, PostcardBackgroundField


class FriendsAppTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()

		result_login = self.client.login(email=self.test_healer.user.email, password='test')
		self.assertTrue(result_login)

		self.emails = ['test@healersource.com', 'test1@healersource.com', 'test2@healersource.com']


class InviteTest(FriendsAppTest):
	def test_invite_view_form(self):
		response = self.client.get(reverse('invite_to_join'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), JoinInviteRequestForm)

	def test_invite_healer_view_form(self):
		response = self.client.get(reverse('invite_healer'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), JoinInviteRequestForm)

	def test_invite_view_form_with_imported_contacts(self):
		imported_contacts = []
		imported_contacts.append(Contact.objects.create(user=self.test_healer.user, name='u1', email='u1@healersource.com').id)
		imported_contacts.append(Contact.objects.create(user=self.test_healer.user, name='u2', email='u2@healersource.com').id)
		session = self.client.session
		session['imported_contacts'] = imported_contacts
		session.save()
		response = self.client.get(reverse('invite_to_join'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['form']), JoinInviteRequestForm)
		self.assertContains(response, "u1@healersource.com\nu2@healersource.com")

	def test_invite_view_post_existing_email(self):
		existing_user = Healer.objects.get(pk=3).user
		EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=True)
		self.emails.append(existing_user.email)

		data = {'emails': ';'.join(self.emails), 'message': 'test', 'invite_type': 'client'}
		response = self.client.post(reverse('invite_to_join'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Contact.objects.filter(email__in=self.emails).count(), 3)

		email = get_email()
		self.assertTrue('has added you as a Client' in email.subject)

	def test_invite_view_post(self):
		message = 'test message'
		data = {'emails': "%s, %s\n%s" % (self.emails[0], self.emails[1], self.emails[2]),
				'message': message,
				'invite_type': 'client'}
		response = self.client.post(reverse('invite_to_join'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Contact.objects.filter(email__in=self.emails).count(), 3)

		email = get_email()
		self.assertNotEqual(email.subject.find('has added you as a Client'), -1)
		self.assertNotEqual(email.body.find(message), -1)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(self.test_healer.invite_message, message)

	def test_invite_email_view(self):
		response = self.client.get(reverse('invite_to_join_emails', args=['test@healersource.com']))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'test@healersource.com')


class InvitePostcardTest(FriendsAppTest):

	def setUp(self):
		super(InvitePostcardTest, self).setUp()
		self.existing_user = Healer.objects.get(pk=3).user
		EmailAddress.objects.create(user=self.existing_user, email=self.existing_user.email, verified=True)

	def test_get(self):
		response = self.client.get(reverse('invite_postcard'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['join_request_form']), ContactsJoinInviteRequestForm)

	def test_post_provider_recommend(self):
		message = 'test\nmessage'
		data = {'email_list': 'new_healer@healersource.com',
				'message': message,
				'invite_type': 'provider',
				'invite_provider_recommend': 'true',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(SiteJoinInvitation.objects.all()[0].create_friendship, True)
		email = get_email()
		self.assertTrue('wants to refer to you' in email.subject)
		message = str(email.message())
		self.assertTrue('To accept this Referral' in message)
		self.assertTrue('To accept this Referral, click here' in message)
		self.assertTrue('test\nmessage' in message)

	def test_post_invite_only(self):
		message = 'test message'
		data = {'email_list': 'new_healer@healersource.com',
				'message': message,
				'invite_type': 'provider',
				'invite_provider_recommend': 'false',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(SiteJoinInvitation.objects.all()[0].create_friendship, False)
		email = get_email()
		self.assertTrue('has invited you' in email.subject)

	def test_post_invite_only_skip_for_client(self):
		message = 'test message'
		data = {'email_list': 'new_healer@healersource.com',
				'message': message,
				'invite_type': 'client',
				'invite_provider_recommend': 'true',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(SiteJoinInvitation.objects.all()[0].create_friendship, True)
		email = get_email()
		self.assertTrue('has added you' in email.subject)
		message = str(email.message())
		self.assertTrue('To accept this invitation' in message)
		self.assertTrue('To accept this invitation, click here' in message)

	def test_get_review(self):
		response = self.client.get(reverse('invite_postcard_review'))
		self.assertEqual(response.status_code, 200)
		self.assertTrue('Invite Your Clients to Review You' in response.content)

	def test_post_review(self):
		message = 'test message'
		data = {'email_list': 'new_healer@healersource.com',
				'message': message,
				'invite_type': 'client',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard_review'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(SiteJoinInvitation.objects.all()[0].create_friendship, True)
		email = get_email()
		self.assertTrue('Please write a Review for' in email.subject)
		message = str(email.message())
		self.assertFalse('To accept this invitation' in message)
		self.assertTrue('To write a review for %s, click here' % title(self.test_healer.user.get_full_name()) in message)

	def test_get_ambassador(self):
		response = self.client.get(reverse('invite_postcard_ambassador'))
		self.assertEqual(response.status_code, 200)

	def test_post_ambassador(self):
		message = 'test message'
		data = {'email_list': 'new_healer@healersource.com',
				'message': message,
				'invite_type': 'client',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard_ambassador'), data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(SiteJoinInvitation.objects.all()[0].create_friendship, True)
		email = get_email()
		self.assertTrue('has invited you to join' in email.subject)
		message = str(email.message())
		self.assertTrue(reverse('ambassador:signup', args=[self.test_healer.user.username]) in message)

	def test_invite_existing_provider(self):
		provider = Healer.objects.get(pk=3)
		message = 'test message'
		data = {'providers': provider.id,
				'message': message,
				'invite_type': 'client',
				'invite_provider_recommend': 'true',
				'postcard_background': PostcardBackgroundField().choices[0][0]}
		response = self.client.post(reverse('invite_postcard'), data)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(SiteJoinInvitation.objects.all().count())
		self.assertFalse(count_emails())
		self.assertContains(response, 'We\'ve added them to your Clients')
		self.assertEqual(Clients.objects.filter(from_user=self.test_healer.user, to_user=provider.user).count(), 1)


class AcceptTest(FriendsAppTest):

	def test_accept_view_invalid_key(self):
		response = self.client.get(reverse('friends_accept_join', args=['test']))

		self.assertEqual(response.status_code, 404)

	def test_accept_view_form(self):
		self.client.logout()
		email = 'test@healersource.com'
		contact, created = Contact.objects.get_or_create(email=email, user=self.test_healer.user)
		SiteJoinInvitation.objects.create(from_user=self.test_healer.user,
									  contact=contact,
									  message="",
									  status="2",
									  confirmation_key="123")
		response = self.client.get(reverse('friends_accept_join', args=['123']))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(type(response.context['client_signup_form']), ClientSignupForm)


class FriendsAppAjaxTest(FriendsAppTest):
	def setUp(self):
		super(FriendsAppAjaxTest, self).setUp()
		self.rest_client = APIClient()
		self.rest_client.force_authenticate(user=self.test_healer.user)


class CreateJoinInvitationAjaxTest(FriendsAppAjaxTest):

	def test_invalid_contact_id(self):
		response = self.rest_client.post(reverse('create_join_invitation'), {'contact_id': 0, 'key': '111'})
		response = json.loads(response.content)
		self.assertEqual(response, 'Could not find that contact.')

	def test_invalid_key(self):
		self.contact = Contact.objects.create(user=self.test_healer.user, name='test')

		response = self.rest_client.post(reverse('create_join_invitation'), {'contact_id': self.contact.id, 'key': ''})
		response = json.loads(response.content)
		self.assertEqual(response, 'Invalid key.')

	def test_success(self):
		self.contact = Contact.objects.create(user=self.test_healer.user, name='test')

		response = self.rest_client.post(reverse('create_join_invitation'), {'contact_id': self.contact.id, 'key': '111'})
		response = json.loads(response.content)

		invitation = SiteJoinInvitation.objects.get(contact=self.contact)
		self.assertEqual(invitation.status, "1")
		self.assertEqual(invitation.confirmation_key, response['confirmation_key'])


class ConfirmSentJoinInvitationAjaxTest(FriendsAppAjaxTest):
	def test_invalid_confirmation_key(self):
		response = self.rest_client.post(reverse('confirm_sent_join_invitation'),
			{'confirmation_key': 'test', 'is_to_healer': False})
		response = json.loads(response.content)
		self.assertEqual(response, 'Could not find that invitation.')

	def test_success(self):
		self.contact = Contact.objects.create(user=self.test_healer.user, name='test')
		self.rest_client.post(reverse('create_join_invitation'),
			{'contact_id': self.contact.id, 'key': '111'})

		invitation = SiteJoinInvitation.objects.get(contact=self.contact)
		self.assertEqual(invitation.status, "1")

		response = self.rest_client.post(reverse('confirm_sent_join_invitation'),
			{'confirmation_key': invitation.confirmation_key, 'is_to_healer': False})
		response = json.loads(response.content)

		invitation = SiteJoinInvitation.objects.get(contact=self.contact)
		self.assertEqual(response['contact_id'], self.contact.id)
		self.assertEqual(invitation.status, "2")


class SendInviteAjaxTest(FriendsAppAjaxTest):
	def test_invalid_email_fail(self):
		data = {'emails': 'test', 'message': 'test message'}
		response = self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})
		response = json.loads(response.content)
		self.assertEqual(response['error_list'], '<li>emails</li>')

	def test_existing_user(self):
		existing_user = Healer.objects.get(pk=3).user
		EmailAddress.objects.create(user=existing_user, email=existing_user.email, verified=True)
		data = {'emails': existing_user.email, 'message': 'test'}
		response = self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})
		response = json.loads(response.content)
		self.assertTrue(response['reload_page'])
		self.assertEqual(Contact.objects.filter(email=existing_user.email).count(), 0)
		self.assertEqual(SiteJoinInvitation.objects.filter(contact__email=existing_user.email).count(), 0)

	def test_new_email(self):
		data = {'emails': 'test@healersource.com', 'message': 'test message'}
		response = self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})
		response = json.loads(response.content)
		self.assertFalse(response['reload_page'])
		self.assertEqual(Contact.objects.filter(email=data['emails']).count(), 1)
		self.assertEqual(SiteJoinInvitation.objects.filter(contact__email=data['emails']).count(), 1)

		email = get_email()
		self.assertNotEqual(email.subject.find('has added you as a Client'), -1)
		self.assertNotEqual(email.body.find(data['message']), -1)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(self.test_healer.invite_message, data['message'])

	def test_existing_invitation(self):
		email = 'test1@healersource.com'
		self.contact = Contact.objects.create(user=self.test_healer.user, name='test', email=email)
		SiteJoinInvitation.objects.create(from_user=self.test_healer.user, contact=self.contact, status="2", confirmation_key="testkey")

		data = {'emails': email, 'message': 'test message'}
		response = self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})
		response = json.loads(response.content)
		self.assertFalse(response['reload_page'])
		invitations = SiteJoinInvitation.objects.filter(contact=self.contact)
		self.assertEqual(invitations.count(), 1)
		self.assertEqual(invitations[0].confirmation_key, 'testkey')

		email = get_email()
		self.assertNotEqual(email.subject.find('has added you as a Client'), -1)
		self.assertNotEqual(email.body.find(data['message']), -1)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(self.test_healer.invite_message, data['message'])

	def test_new_invitation(self):
		email = 'test1@healersource.com'
		self.contact = Contact.objects.create(user=self.test_healer.user, name='test', email=email)

		data = {'emails': email, 'message': 'test message'}
		response = self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})
		response = json.loads(response.content)
		self.assertFalse(response['reload_page'])
		invitations = SiteJoinInvitation.objects.filter(contact=self.contact)
		self.assertEqual(invitations.count(), 1)
		self.assertEqual(invitations[0].status, "2")

		email = get_email()
		self.assertNotEqual(email.subject.find('has added you as a Client'), -1)
		self.assertNotEqual(email.body.find(data['message']), -1)

		self.test_healer = Healer.objects.get(pk=self.test_healer.pk)
		self.assertEqual(self.test_healer.invite_message, data['message'])

	def test_message_saved(self):
		self.test_healer.invite_message = "123"
		self.test_healer.save()

		data = {'emails': 'test@healersource.com', 'message': 'test message'}
		self.rest_client.post(reverse('send_invite'),
			{'data': urllib.urlencode(data)})

		self.assertEqual(Healer.objects.get(id=self.test_healer.id).invite_message, data['message'])


class InviteHealerByHealerTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'treatments.json']

	def setUp(self):
		self.healer = Healer.objects.get(pk=1)
		self.healer.user.set_password('test')
		self.healer.user.save()

		result_login = self.client.login(email=self.healer.user.email, password='test')
		self.assertTrue(result_login)

	def test_existing_healer(self):
		healer2 = Healer.objects.get(pk=3)
		EmailAddress.objects.create(user=healer2.user, email=healer2.user.email, verified=True, primary=True)

		response = self.client.post(reverse('invite_healer'), {'emails': healer2.user.email, 'invite_type': 'provider'}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'We\'ve added them to your Referrals')
		self.assertEqual(Referrals.objects.filter(from_user=self.healer.user, to_user=healer2.user).count(), 1)

	def test_existing_client(self):
		client2 = Client.objects.get(pk=5)
		EmailAddress.objects.create(user=client2.user, email=client2.user.email, verified=True, primary=True)

		response = self.client.post(reverse('invite_healer'), {'emails': client2.user.email, 'invite_type': 'provider'}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'We\'ve added them to your Clients')
		self.assertEqual(Clients.objects.filter(from_user=self.healer.user, to_user=client2.user).count(), 1)

	def test_new_user(self):
		email = 'new_user@healersource.com'
		response = self.client.post(reverse('invite_healer'), {'emails': email, 'invite_type': 'provider'}, follow=True)

		self.assertEqual(response.status_code, 200)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.healer.user, contact__email=email, is_to_healer=True)
		self.assertEqual(invitation.count(), 1)

	def test_dummy_user(self):
		email = 'dummy_user@healersource.com'
		user = User.objects.create(email=email, is_active=False)
		user.set_unusable_password()
		user.save()
		Client.objects.create(user=user)

		response = self.client.post(reverse('invite_healer'), {'emails': email, 'invite_type': 'provider'}, follow=True)

		self.assertEqual(response.status_code, 200)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.healer.user, contact__email=email, is_to_healer=True)
		self.assertEqual(invitation.count(), 1)


class InviteClientByHealerTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'treatments.json']

	def setUp(self):
		self.healer = Healer.objects.get(pk=1)
		self.healer.user.set_password('test')
		self.healer.user.save()

		result_login = self.client.login(email=self.healer.user.email, password='test')
		self.assertTrue(result_login)

	def test_existing_healer(self):
		healer2 = Healer.objects.get(pk=3)
		EmailAddress.objects.create(user=healer2.user, email=healer2.user.email, verified=True, primary=True)

		response = self.client.post(reverse('invite_to_join'), {'emails': healer2.user.email, 'invite_type': 'client'}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'We\'ve added them to your Clients')
		self.assertEqual(Clients.objects.filter(from_user=self.healer.user, to_user=healer2.user).count(), 1)

	def test_existing_client(self):
		client2 = Client.objects.get(pk=5)
		EmailAddress.objects.create(user=client2.user, email=client2.user.email, verified=True, primary=True)

		response = self.client.post(reverse('invite_to_join'), {'emails': client2.user.email, 'invite_type': 'client'}, follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'We\'ve added them to your Clients')
		self.assertEqual(Clients.objects.filter(from_user=self.healer.user, to_user=client2.user).count(), 1)

	def test_new_user(self):
		email = 'new_user@healersource.com'
		response = self.client.post(reverse('invite_to_join'), {'emails': email, 'invite_type': 'client'}, follow=True)
		self.assertEqual(response.status_code, 200)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.healer.user, contact__email=email, is_to_healer=False)
		self.assertEqual(invitation.count(), 1)

	def test_dummy_user(self):
		email = 'dummy_user@healersource.com'
		user = User.objects.create(email=email, is_active=False)
		user.set_unusable_password()
		user.save()
		Client.objects.create(user=user)

		response = self.client.post(reverse('invite_to_join'), {'emails': email, 'invite_type': 'client'}, follow=True)

		self.assertEqual(response.status_code, 200)

		invitation = SiteJoinInvitation.objects.filter(from_user=self.healer.user, contact__email=email, is_to_healer=False)
		self.assertEqual(invitation.count(), 1)


class RecommendationsTest(test.TestCase):

	def setUp(self):
		self.healers = []
		for i in range(10):
			h = G(Healer, profileVisibility=Healer.VISIBLE_EVERYONE, about='test').user
			G(Avatar, user=h)
			self.healers.append(h)

		self.zipcodes = [
			G(Zipcode, code='10001', point=Point(-73.99, 40.71)),
			G(Zipcode, code='20001', point=Point(-77.03, 38.89))
		]

class ProviderRecommendationsTest(RecommendationsTest):

	def setUp(self):
		super(ProviderRecommendationsTest, self).setUp()

		self.request = HttpRequest
		self.request.user = self.healers[0]

	def test_direct_recommendations(self):
		G(Referrals, from_user=self.healers[0], to_user=self.healers[1])
		G(Referrals, from_user=self.healers[1], to_user=self.healers[2]) #1
		G(Referrals, from_user=self.healers[1], to_user=self.healers[3]) #2
		G(Referrals, from_user=self.healers[0], to_user=self.healers[4])
		G(Referrals, from_user=self.healers[4], to_user=self.healers[5]) #3

		rf = ProviderRecommendationsFinder(self.request, recommendations_limit=4)
		self.assertEqual(len(rf.recommendations), 4)
		#they are random, not needed for now
		#self.assertTrue(self.healers[2] in rf.recommendations)
		#self.assertTrue(self.healers[3] in rf.recommendations)
		#self.assertTrue(self.healers[5] in rf.recommendations)

	def test_geosearch(self):
		location1 = G(Location, point=self.zipcodes[0].point, postal_code=self.zipcodes[0].code)
		location2 = G(Location, point=self.zipcodes[1].point, postal_code=self.zipcodes[1].code)
		G(Referrals, from_user=self.healers[0], to_user=self.healers[1])
		G(ClientLocation, client=self.healers[1].client, location=location1)
		G(ClientLocation, client=self.healers[2].client, location=location1) #1
		G(ClientLocation, client=self.healers[3].client, location=location1) #2
		G(ClientLocation, client=self.healers[4].client, location=location2)

		rf = ProviderRecommendationsFinder(self.request, recommendations_limit=3)
		self.assertEqual(len(rf.recommendations), 3)
		#they are random, not needed for now
		#self.assertTrue(self.healers[2] in rf.recommendations)
		#self.assertTrue(self.healers[3] in rf.recommendations)

	def test_limit(self):
		location1 = G(Location, point=self.zipcodes[0].point, postal_code=self.zipcodes[0].code)
		G(Referrals, from_user=self.healers[0], to_user=self.healers[1])
		G(Referrals, from_user=self.healers[1], to_user=self.healers[2]) #1
		G(Referrals, from_user=self.healers[1], to_user=self.healers[7]) #2
		G(ClientLocation, client=self.healers[1].client, location=location1)
		G(ClientLocation, client=self.healers[3].client, location=location1) #3
		G(ClientLocation, client=self.healers[4].client, location=location1) #4
		G(ClientLocation, client=self.healers[5].client, location=location1) #5
		G(ClientLocation, client=self.healers[6].client, location=location1) #6

		rf = ProviderRecommendationsFinder(self.request)
		self.assertEqual(len(rf.recommendations), rf.recommendations_limit)
