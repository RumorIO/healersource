from django.http import HttpRequest

from avatar.models import Avatar
from django import test
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from emailconfirmation.models import EmailAddress
from friends.models import Contact
from oauth_access.access import OAuthAccess
from clients.models import SiteJoinInvitation
from contacts_hs.models import ContactsImportStatus, FACEBOOK_API, STATUS_RUNNING
from healers.models import is_healer
from sync_hs.facebook import save_facebook_data, save_facebook_picture, save_facebook_friends_to_contacts, facebook_callback


class FacebookHandleNoUserTest(test.TestCase):
	"""
		Create new user
	"""
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		self.request = HttpRequest()
		self.request.user = AnonymousUser()
		self.request.session = SessionStore()

		self.oauth_access = OAuthAccess(service='facebook')

	def test_no_join_invitation_success(self):
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': 'test1@healersource.com', 'id': '1'}
		user = facebook_callback.handle_no_user(self.request, self.oauth_access, fb_data, 'healer')

		self.assertEqual(user.email, fb_data['email'])
		self.assertFalse(user.has_usable_password())
		self.assertTrue(user.is_active)

		self.assertTrue(is_healer(user.client))

	def test_exist_user_by_email_success(self):
		EmailAddress.objects.create(user=User.objects.get(id=1), email='daniel@innergraphics.com', verified=True)
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': 'daniel@innergraphics.com', 'id': '1'}
		user = facebook_callback.handle_no_user(self.request, self.oauth_access, fb_data, 'healer')

		self.assertEqual(User.objects.get(id=1), user)

	def test_join_invitation_success(self):
		from_user = User.objects.get(id=1)
		email = 'test@healersource.com'
		contact, created = Contact.objects.get_or_create(email=email, user=from_user)
		SiteJoinInvitation.objects.create(from_user=from_user,
			contact=contact,
			message="",
			status="2",
			confirmation_key="123",
			is_to_healer=True)

		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': email, 'id': '1'}
		user = facebook_callback.handle_no_user(self.request, self.oauth_access, fb_data, 'healer')

		self.assertEqual(user.email, fb_data['email'])
		self.assertFalse(user.has_usable_password())
		self.assertTrue(user.is_active)
		self.assertTrue(is_healer(user.client))


class SaveFacebookDataTest(test.TestCase):
	"""
		Import data for user - daniel@innergraphics.com
	"""
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		self.user = User.objects.get(pk=1)

	def test_original_data_not_replaced(self):
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': ''}
		save_facebook_data(self.user, fb_data)

		updated_user = User.objects.get(pk=1)
		self.assertEqual(self.user.first_name, updated_user.first_name)
		self.assertEqual(self.user.last_name, updated_user.last_name)

	def test_empty_data_filled(self):
		self.user.first_name = ""
		self.user.last_name = ""
		self.user.save()
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': ''}
		save_facebook_data(self.user, fb_data)

		updated_user = User.objects.get(pk=1)
		self.assertEqual(fb_data['first_name'], updated_user.first_name)
		self.assertEqual(fb_data['last_name'], updated_user.last_name)

	def test_email_skipped(self):
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': self.user.email}
		save_facebook_data(self.user, fb_data)

		self.assertEqual(EmailAddress.objects.filter(user=self.user).count(), 0)

	def test_email_added(self):
		fb_data = {'first_name': 'test1', 'last_name': 'test2', 'email': 'test1@healersource.com'}
		save_facebook_data(self.user, fb_data)

		self.assertEqual(EmailAddress.objects.filter(user=self.user, email='test1@healersource.com').count(), 1)

	def test_avatar_skipped(self):
		avatar = Avatar(user=self.user, avatar='test')
		avatar.save()
		save_facebook_picture(self.user, '100001967605350')

		self.assertEqual(Avatar.objects.get(user=self.user).avatar, 'test')

	def test_avatar_added(self):
		save_facebook_picture(self.user, '100001967605350')
		self.assertEqual(Avatar.objects.filter(user=self.user).count(), 1)


class ImportContactsTest(test.TestCase):
	"""
		Import contacts for user - daniel@innergraphics.com
	"""
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		self.user = User.objects.get(pk=1)

	def test_facebook_existing_user(self):
		"""
		test import existing user frank@healersource.com from facebook
		"""
		import_status = ContactsImportStatus.objects.create(user=self.user, api=FACEBOOK_API, status=STATUS_RUNNING)
		fb_friends = [{'name': 'test1', 'id': 'fb_test1'}, {'name': 'frankus cattus', 'id': 'fb_test2'}]
		save_facebook_friends_to_contacts(self.user, fb_friends, import_status, True)

		contacts = Contact.objects.filter(user=self.user)
		self.assertEqual(contacts.count(), 2)

#		test1 = contacts.get(name='test1')
#		self.assertEqual(test1.contactsocialid_set.get(service='facebook').social_id, 'fb_test1')
#
#		friendship = Clients.objects.filter(from_user=self.user, to_user=User.objects.filter(email='frank@healersource.com'))
#		self.assertEqual(friendship.count(), 1)

#	def test_facebook_then_google(self):
#		"""
#		test import from facebook first, then from google
#		"""
#		fb_friends = [{'name': 'test1', 'id': 'fb_test1'}, {'name': 'test2', 'id': 'fb_test2'}]
#		save_facebook_friends_to_contacts(self.user, fb_friends)
#
#		contacts = Contact.objects.filter(user = self.user)
#		self.assertEqual(contacts.count(), 2)
#
#		test1 = contacts.get(name='test1')
#		self.assertEqual(test1.contactsocialid_set.get(service='facebook').social_id, 'fb_test1')
#
#		# new
#		entry1 = PersonEntry()
#		entry1.id = Id(text="google_test3")
#		entry1.title = Title(text="test3")
#		entry1.email = [gdata.data.Email(address="test3@healersource.com", primary=True)]
#
#		# merge with fb
#		entry2 = PersonEntry()
#		entry2.id = Id(text="google_test4")
#		entry2.title = Title(text="test1")
#		entry2.email = [gdata.data.Email(address="test1@healersource.com")]
#
#		# skip
#		entry3 = PersonEntry()
#		entry3.id = Id(text="google_test5")
#		entry3.title = Title(text="test5")
#		entry3.email = []
#
#		google_entries = [entry1, entry2, entry3]
#		save_google_entries_to_contacts(self.user, google_entries)
#
#		contacts = Contact.objects.filter(user = self.user)
#		self.assertEqual(contacts.count(), 3)
#
#		test3 = contacts.get(name='test3')
#		self.assertEqual(test3.email, 'test3@healersource.com')
#		self.assertEqual(test3.contactsocialid_set.get(service='google').social_id, 'google_test3')
#
#		test1 = contacts.get(name='test1')
#		self.assertEqual(test1.email, 'test1@healersource.com')
#		self.assertEqual(test1.contactsocialid_set.get(service='google').social_id, 'google_test4')
#		self.assertEqual(test1.contactsocialid_set.get(service='facebook').social_id, 'fb_test1')

#	def test_google_then_facebook(self):
#		"""
#		test import from google first, then from facebook
#		"""
#		entry1 = PersonEntry()
#		entry1.id = Id(text="google_test3")
#		entry1.title = Title(text="test3")
#		entry1.email = [gdata.data.Email(address="test3@healersource.com", primary=True)]
#
#		entry2 = PersonEntry()
#		entry2.id = Id(text="google_test4")
#		entry2.title = Title(text="test1")
#		entry2.email = [gdata.data.Email(address="test1@healersource.com")]
#
#		# skip
#		entry3 = PersonEntry()
#		entry3.id = Id(text="google_test5")
#		entry3.title = Title(text="test5")
#		entry3.email = []
#
#		google_entries = [entry1, entry2, entry3]
#		save_google_entries_to_contacts(self.user, google_entries)
#
#		contacts = Contact.objects.filter(user = self.user)
#		self.assertEqual(contacts.count(), 2)
#
#		test1 = contacts.get(name='test1')
#		self.assertEqual(test1.email, 'test1@healersource.com')
#		self.assertEqual(test1.contactsocialid_set.get(service='google').social_id, 'google_test4')
#
#		# one merge, one add
#		fb_friends = [{'name': 'test1', 'id': 'fb_test1'}, {'name': 'test2', 'id': 'fb_test2'}]
#		save_facebook_friends_to_contacts(self.user, fb_friends)
#
#		contacts = Contact.objects.filter(user = self.user)
#		self.assertEqual(contacts.count(), 3)
#
#		test1 = contacts.get(name='test1')
#		self.assertEqual(test1.email, 'test1@healersource.com')
#		self.assertEqual(test1.contactsocialid_set.get(service='google').social_id, 'google_test4')
#		self.assertEqual(test1.contactsocialid_set.get(service='facebook').social_id, 'fb_test1')


#	def test_google_existing_user(self):
#		"""
#		test import existing user frank@healersource.com from google
#		"""
#		Clients.objects.filter(from_user=self.user).delete()
#
#		entry1 = PersonEntry()
#		entry1.id = Id(text="google_test3")
#		entry1.title = Title(text="test3")
#		entry1.email = [gdata.data.Email(address="test3@healersource.com", primary=True)]
#
#		entry2 = PersonEntry()
#		entry2.id = Id(text="google_test4")
#		entry2.title = Title(text="frankus cattus")
#		entry2.email = [gdata.data.Email(address="frank@healersource.com")]
#
#		google_entries = [entry1, entry2]
#		save_google_entries_to_contacts(self.user, google_entries)
#
#		contacts = Contact.objects.filter(user = self.user)
#		self.assertEqual(contacts.count(), 1)
#
#		test3 = contacts.get(name='test3')
#		self.assertEqual(test3.email, 'test3@healersource.com')
#		self.assertEqual(test3.contactsocialid_set.get(service='google').social_id, 'google_test3')
#
#		friendship = Clients.objects.filter(from_user=self.user, to_user=User.objects.filter(email='frank@healersource.com'))
#		self.assertEqual(friendship.count(), 1)
