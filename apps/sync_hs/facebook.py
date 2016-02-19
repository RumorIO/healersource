import os
import urllib
import requests
import imghdr
import json

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.utils import DatabaseError
from django.conf import settings
from django.shortcuts import redirect

from avatar.models import Avatar
from friends.models import Contact, EmailAddress
from pinax.apps.account.utils import get_default_redirect
from oauth_access.access import OAuthAccess, OAuth20Token
from oauth_access.models import UserAssociation
from oauth_access.callback import AuthenticationCallback

from util import is_correct_image_file_type
from clients.models import create_dummy_user, ClientLocation
from clients.utils import avatar_file_path
from contacts_hs.models import (ContactSocialId, ContactsImportStatus,
	FACEBOOK_API, STATUS_RUNNING, STATUS_DONE, STATUS_FAIL)
from healers.models import Location, is_healer
from healers.threads import run_in_thread
from account_hs.utils import (set_signup_source, post_signup_processing,
							after_signup)
from ambassador.handlers import set_ambassador


class FacebookAuthError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class FacebookNoEmail(Exception):
	pass


def get_facebook_auth_url(request, url_name, args=None):
	oauth_access = OAuthAccess(service="facebook")
	facebook_redirect_url = request.build_absolute_uri(reverse(url_name, args=args))
	facebook_auth_url = '%s?client_id=%s&redirect_uri=%s&display=page' % (oauth_access.authorize_url,
	                                                                      oauth_access.key,
	                                                                      facebook_redirect_url)
	return facebook_auth_url


def save_facebook_data(user, fb_data, save_location=False, save_website=False):
	if not user.first_name:
		user.first_name = fb_data.get('first_name', "")
	if not user.last_name:
		user.last_name = fb_data.get('last_name', "")
	user.save()

	fb_email = fb_data.get('email', None)
	if fb_email and user.email != fb_email:
		try:
			email = EmailAddress.objects.filter(user=user, email__iexact=fb_email)[0]
			if not email.verified:
				email.verified = True
				email.save()
		except IndexError:
			EmailAddress.objects.create(user=user, email=fb_email, verified=True)

	client = user.client
	client.facebook = fb_data.get('link', "")
	if save_website and 'website' in fb_data:
		client.website = fb_data['website']
	client.save()

	if save_location and 'location' in fb_data:
		try:
			ClientLocation.objects.filter(client=client, location__city=fb_data['location']['name'])[0]
		except IndexError:
			location = Location.objects.create(city=fb_data['location']['name'])
			ClientLocation.objects.create(client=client, location=location)


def save_facebook_picture(user, fb_id, token="", check_avatar=True):
	if check_avatar and Avatar.objects.filter(user=user).count():
		return

	args = {"width": "420", "access_token": token}
	url = "https://graph.facebook.com/" + fb_id + "/picture?" + urllib.urlencode(args)
	file = urllib.urlopen(url)
	file_contents = file.read()
	file_type = imghdr.what('', file_contents)
	if not is_correct_image_file_type(file_type):
		return
	avatar_path = avatar_file_path(user, file_type, fb_id)
	full_path = os.path.join(settings.MEDIA_ROOT, avatar_path)
	head = os.path.split(full_path)[0]

	try:
		if not os.path.exists(head):
			os.makedirs(head)
		local_file = open(full_path, "wb")
		local_file.write(file_contents)
		local_file.close()
		avatar = Avatar(
			user=user,
			primary=True,
			avatar=avatar_path,
		)
		avatar.save()
	except Exception:
		pass
	finally:
		file.close()


@run_in_thread
def save_facebook_friends_thread(user, import_status, token, request=None):
	if request:
		request.session['import_fb_friends_started'] = True
	save_facebook_friends(user, import_status, token)
	if request:
		del request.session['import_fb_friends_started']


def save_facebook_friends(user, import_status, token):
	try:
		friends = load_facebook_friends(token)
		contacts = save_facebook_friends_to_contacts(user, friends, import_status)
	except Exception as e:
		import_status.status = STATUS_FAIL
		import_status.save()
		raise e

	return contacts


def save_facebook_friends_to_contacts(user, friends, import_status, is_test=False):
	def get_point():
		url = "https://graph.facebook.com/%s?access_token=%s" % (friend['id'], token)
		response = requests.get(url).json()
		if 'location' in response:
			location_id = response['location']['id']
			url = "https://graph.facebook.com/%s?access_token=%s" % (location_id, token)
			response = requests.get(url).json()
			if 'location' in response:
				return Point(response['location']['latitude'], response['location']['longitude'])

	contacts = []
	if not is_test:
		token = user.userassociation_set.get(service='facebook').token
	for friend in friends:
		point = None
		if not is_test:
			point = get_point()
		try:
			try:
				obj = ContactSocialId.objects.filter(contact__user=user, social_id=friend['id'], service="facebook")[0]
			except IndexError:
				try:
					contact = Contact.objects.filter(user=user, name=friend['name'])[0]
				except IndexError:
					contact = Contact.objects.create(user=user, name=friend['name'])
					contacts.append(contact)
				obj, created = ContactSocialId.objects.get_or_create(
					contact=contact, service="facebook", social_id=friend['id'])
			if point:
				obj.point = point
				obj.save()
		except DatabaseError:
			try:
				transaction.rollback()
			except Exception:
				pass
			continue
		import_status.contacts_count += 1
		import_status.save()

	import_status.status = STATUS_DONE
	import_status.save()

	return contacts


def load_facebook_friends(token, next_url=None):
	args = {"access_token": token, 'limit': 50}
	url = next_url if next_url else "https://graph.facebook.com/me/friends?" + urllib.urlencode(args)
	file = urllib.urlopen(url)
	try:
		response = json.loads(file.read())
	finally:
		file.close()

	if response.get('error', False):
		msg = response['error'].get('message', '')
		if response['error'].get('type', '') == 'OAuthException':
			raise FacebookAuthError(msg)
		else:
			raise Exception(msg)

	if 'next' in response['paging']:
		return response['data'] + load_facebook_friends(token, response['paging']['next'])
	return response['data']


def load_facebook_user_data(token):
	access = OAuthAccess(service="facebook")
	fb = FacebookCallback()
	response = fb.fetch_user_data(None, access, OAuth20Token(token))
	if response and response.get('error', False):
		msg = response['error'].get('message', '')
		if response['error'].get('type', '') == 'OAuthException':
			raise FacebookAuthError(msg)
		else:
			raise Exception(msg)


class FacebookCallback(AuthenticationCallback):
	def __call__(self, request, access, token, account_type=None, is_ajax=False,
				is_signup=False, is_ambassador=False, is_phonegap=False):
		user_data = self.fetch_user_data(request, access, token)
		if 'error' in user_data:
			if is_ajax:
				return None, "Error during facebook login."
			return redirect('login_page')

		redirect_to = self.redirect_url(request)
		if not request.user.is_authenticated():
			try:
				user = self.lookup_user(request, access, user_data)
			except FacebookNoEmail:
				message = (
					"Your Facebook account does not have an email "
					"associated with it, so you must sign up "
					"using the regular signup form. "
					"Thanks and sorry for the inconvenience.")
				if is_ajax:
					return None, message
				request.session['oauth_error_message'] = message
				return redirect('oauth_error')
			if user is None:
				if is_ajax and not is_signup:
					return None, "You have no account on healersouce.com"
				if not account_type:
					request.session["token"] = token
					return redirect('select_account_type', access.service)
				else:
					user = self.handle_no_user(request, access, user_data, account_type, is_ambassador, is_phonegap)
			else:
				user = self.handle_unauthenticated_user(request, user, access, token, user_data)
		else:
			user = access.lookup_user(identifier=self.identifier_from_data(user_data))
			if user and user != request.user:
				facebook_associate_new_account = request.session.pop('facebook_associate_new_account', False)
				if facebook_associate_new_account:
					ua = UserAssociation.objects.filter(user=user, service="facebook")[0]
					ua.user = request.user
					ua.save()
				else:
					message = "There is another user connected to this account on facebook."
					if is_ajax:
						return None, message
					request.session['oauth_error_message'] = message
					request.session['oauth_error_is_facebook_duplicate'] = True
					return redirect('oauth_error')

			user = request.user

		if user:
			kwargs = {"identifier": self.identifier_from_data(user_data)}

			# for first time, save fb data, load fb friends for healer
			ua = UserAssociation.objects.filter(user=user, service="facebook")
			if not ua.count():
				save_facebook_data(user, user_data)
				save_facebook_picture(user, user_data['id'], token)
			if is_healer(user.client) or "send_healing_facebook" in request.session:
				ContactsImportStatus.objects.filter(user=user).delete()
				import_status = ContactsImportStatus.objects.create(user=user, api=FACEBOOK_API, status=STATUS_RUNNING)
				save_facebook_friends_thread(user, import_status, token, request)

			access.persist(user, token, **kwargs)

		if "send_healing_facebook" in request.session:
			del request.session["send_healing_facebook"]
			request.session['got_friends_from_fb'] = True
			redirect_to = reverse("send_healing")
		if is_ajax:
			set_signup_source(user, request, is_phonegap)
			return user, None
		return redirect(redirect_to)

	def handle_unauthenticated_user(self, request, user, access, token, user_data):
		self.login_user(request, user)
		return user

	def handle_no_user(self, request, access, user_data, account_type, is_ambassador=False, is_phonegap=False):
		user = self.lookup_user(request, access, user_data)
		if user is None:
			user = create_dummy_user(user_data.get('first_name', ""), user_data.get('last_name', ""),
				user_data['email'], False, account_type in ['healer', 'wellness_center'])
			user.is_active = True
			user.save()

			EmailAddress.objects.create(user=user, email=user_data['email'], verified=True, primary=True)

			after_signup(user, account_type=account_type)
			post_signup_processing(user, is_ambassador, request.session)

			set_ambassador(
				client_user=user,
				cookies=request.COOKIES)

			if not is_phonegap:
				self.login_user(request, user)
		return user

	def lookup_user(self, request, access, user_data):
		# find user by facebook id
		user = access.lookup_user(identifier=self.identifier_from_data(user_data))
		if user:
			return user

		# find user by verified email
		if 'email' in user_data:
			email = user_data['email']
		else:
			raise FacebookNoEmail()
		try:
			user = EmailAddress.objects.filter(email__iexact=email, verified=True)[0].user
			if not user.is_active:
				return None
			return user
		except IndexError:
			return None

	def fetch_user_data(self, request, access, token):
		url = "https://graph.facebook.com/me"
		return access.make_api_call("json", url, token)

	def identifier_from_data(self, data):
		return "fb-%s" % data["id"]

	def redirect_url(self, request):
		# if "send_healing_facebook" in request.session:
		# 	del request.session["send_healing_facebook"]
		# 	return reverse("send_healing")
		return request.session.pop('oauth_callback_redirect', get_default_redirect(request, '/'))

facebook_callback = FacebookCallback()
