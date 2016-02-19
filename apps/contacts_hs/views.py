import oauth2client
import io
import csv

from django.core.validators import validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.utils import DatabaseError
from django.http import Http404
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import TemplateView
from django.template import RequestContext

from friends.models import Contact
from oauth_access.models import UserAssociation
from rest_framework.response import Response

from account_hs.authentication import user_authenticated
from account_hs.views import UserAuthenticated, UserLoggedIn
from clients.models import Client, create_dummy_user, ClientPhoneNumber
from healers.models import is_healer, is_my_client, Healer, Clients
from healers.views import friends
from healers.threads import run_in_thread
from sync_hs.facebook import (FacebookAuthError, save_facebook_friends_thread,
	load_facebook_user_data, save_facebook_picture)

from contacts_hs.models import (ContactInfo, ContactEmail, ContactPhone,
	ContactGroup, ContactsImportStatus, GOOGLE_API, STATUS_RUNNING,
	STATUS_DONE, STATUS_FAIL, ContactSocialId, FACEBOOK_API)
from contacts_hs.gcontacts import GoogleContacts


@run_in_thread
def import_google_contact_process(healer, google_contacts, import_status):
	try:
		groups = google_contacts.get_groups()
		groups_by_id = {}
		for group_dict in groups:
			try:
				try:
					group = ContactGroup.objects.get(google_id=group_dict['google_id'])
					group.name = group_dict['name']
					group.save()
				except ContactGroup.DoesNotExist:
					group = ContactGroup.objects.create(google_id=group_dict['google_id'],
						name=group_dict['name'])
			except DatabaseError:
				try:
					transaction.rollback()
				except Exception:
					pass
				continue
			groups_by_id[group_dict['google_id']] = group

		contacts = google_contacts.get()
		for contact_dict in contacts:
			if not contact_dict.get('primary_email', False):
				continue

			try:
				try:
					contact = Contact.objects.get(user=healer.user, email=contact_dict['primary_email'])
					try:
						contact_info = ContactInfo.objects.get(contact=contact, healer=healer)
					except ContactInfo.DoesNotExist:
						contact_info = ContactInfo()
				except Contact.DoesNotExist:
					contact = Contact.objects.create(user=healer.user,
						name=contact_dict['name'],
						email=contact_dict['primary_email'])
					contact_info = ContactInfo()

				try:
					client = Client.objects.get(user__email=contact.email)
				except Client.DoesNotExist:
					client = None

				contact_info.contact = contact
				contact_info.client = client
				contact_info.healer = healer
				contact_info.first_name = contact_dict.get('first_name', '')
				contact_info.last_name = contact_dict.get('last_name', '')
				contact_info.save()

				ContactEmail.objects.filter(contact=contact_info).delete()
				for email in contact_dict['emails']:
					if email[0] != contact_dict['primary_email']:
						ContactEmail.objects.create(contact=contact_info, email=email[0], type=email[1])

				ContactPhone.objects.filter(contact=contact_info).delete()
				for phone in contact_dict['phones']:
					ContactPhone.objects.create(contact=contact_info, number=phone[0], type=phone[1])

				ContactSocialId.objects.get_or_create(contact=contact, service="google",
					social_id=contact_dict['id'])

				for group_id in contact_dict['groups']:
					groups_by_id[group_id].contacts.add(contact_info)
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
	except Exception:
		try:
			transaction.rollback()
		finally:
			import_status.status = STATUS_FAIL
			import_status.save()


@login_required
def import_google_contacts(request):
	if not is_healer(request.user):
		raise Http404

	try:
		google_contacts = GoogleContacts(request.user)
	except oauth2client.client.Error:
		request.session['oauth_callback_redirect'] = 'import_google_contacts'
		return redirect('oauth2_google_login')

	healer = request.user.client.healer

	# check running import from any api
	import_status = ContactsImportStatus.objects.filter(user=healer.user,
		status=STATUS_RUNNING)
	if import_status.count() > 0:
		return redirect('import_contacts_status')

	# remove all previous statuses and run
	ContactsImportStatus.objects.filter(user=healer.user).delete()
	import_status = ContactsImportStatus.objects.create(user=healer.user,
		api=GOOGLE_API, status=STATUS_RUNNING)
	import_google_contact_process(healer, google_contacts, import_status)

	response = redirect('import_contacts_status')
	if request.GET.get('fb', 0):
		response['Location'] += '?fb=1'
	return response


@login_required
def import_facebook_photo(request):
	try:
		ua = UserAssociation.objects.get(user=request.user, service='facebook')
		save_facebook_picture(request.user, ua.identifier.replace('fb-', ''),
			ua.token, check_avatar=False)
		import_facebook_contacts(request)
		return redirect(request.GET.get('next', 'avatar_change'))
	except (FacebookAuthError, UserAssociation.DoesNotExist):
		request.session['oauth_callback_redirect'] = 'import_facebook_photo'
		return redirect('oauth_access_login', 'facebook')


@login_required
def import_facebook_contacts(request):
	is_floatbox = request.GET.get('fb', 0)
	try:
		is_floatbox = int(is_floatbox)
	except ValueError:
		is_floatbox = 0

	# check running import from any api
	import_status = ContactsImportStatus.objects.filter(user=request.user,
		status=STATUS_RUNNING)
	if import_status.count() > 0:
		return redirect('import_contacts_status')

	try:
		ua = UserAssociation.objects.get(user=request.user, service='facebook')
		load_facebook_user_data(ua.token)  # to check access
		ContactsImportStatus.objects.filter(user=request.user).delete()
		import_status = ContactsImportStatus.objects.create(user=request.user,
			api=FACEBOOK_API, status=STATUS_RUNNING)
		save_facebook_friends_thread(request.user, import_status, ua.token)
		response = redirect('import_contacts_status')
		if is_floatbox:
			response['Location'] += '?fb=1'
		return response
	except (FacebookAuthError, UserAssociation.DoesNotExist):
		oauth_callback_redirect = reverse('import_facebook_contacts')
		if is_floatbox:
			oauth_callback_redirect += '?fb=1'
		request.session['oauth_callback_redirect'] = 'import_facebook_contacts'
		return redirect('oauth_access_login', 'facebook')


def is_valid_email(email):
	try:
		validate_email(email)
		return email
	except ValidationError:
		return ''


def get_csv_contacts(_file):
	''' Return List on success and String on error'''

	def read_csv():
		''' Return List on success and String on error'''

		def _utf_8_encoder(unicode_csv_data):
			for line in unicode_csv_data:
				yield line.encode('utf-8')

		try:
			dialect = csv.Sniffer().sniff(_file.read(1024))
		except Exception as e:
			return e.args[0]

		_file.seek(0)
		reader = csv.reader(_utf_8_encoder(_file), dialect)
		output = []

		try:
			for row in reader:
				output.append(row)
		except csv.Error as e:
			return 'line %d: %s' % (reader.line_num, e)
		return output

	def get_contacts(csv):
		''' Return List on success and String on error'''

		KEYS = ['first name', 'last name', 'email', 'phone']

		if len(csv[0]) < 3:
			return 'The CSV file contains less than 3 columns.'

		def remove_first_row_if_email_is_not_valid(csv):
			if not is_valid_email(csv[0][2]):
				csv.pop(0)

		remove_first_row_if_email_is_not_valid(csv)

		contacts = []
		for contact_data in csv:
			contact = {}
			for n in range(min(len(contact_data), len(KEYS))):
				contact[KEYS[n]] = contact_data[n]
			contacts.append(contact)
		return contacts

	csv_data = read_csv()
	if type(csv_data) == str:
		return csv_data
	else:
		return get_contacts(csv_data)


@user_authenticated
def import_csv_contacts(request):
	def import_contacts(contacts):
		def import_contact(contact):
			user = None
			healer = get_object_or_404(Healer, user=request.user)
			first_name = contact['first name']
			last_name = contact['last name']
			email = contact['email']
			phone = contact.get('phone', None)

			# skip if there is no first name
			if first_name == '':
				return

			email = is_valid_email(email)
			if email:
				user = User.objects.filter(email__iexact=email)
				if user.exists():
					user = user[0]

			if not user:
				user = create_dummy_user(first_name, last_name, email)

			# if can't find or create user, skip
			if not user:
				return

			is_client = is_my_client(healer.user, user)

			# if client created by healer
			if not is_client:
				friendship = Clients(from_user=healer.user, to_user=user)
				friendship.save()

			try:
				client = Client.objects.get(user=user)
			except ObjectDoesNotExist:
				client = Client(user=user)
				client.approval_rating = 100
				client.save()
			contact_info = client.get_contact_info(healer)
			if not contact_info:
				contact_info = ContactInfo.objects.create(
					healer=healer,
					client=client,
					first_name=user.first_name,
					last_name=user.last_name)
				contact_info.emails.add(ContactEmail(email=user.email))
			if phone:
				client.phone_numbers.add(ClientPhoneNumber(number=phone))
				contact_info.phone_numbers.add(ContactPhone(number=phone))

		for contact in contacts:
			import_contact(contact)

	error = None
	if request.FILES:
		im_file = request.FILES['csv']

		if im_file.name.split('.')[-1].lower() == 'csv':
			_file = io.StringIO(unicode(im_file.read(), 'utf-8', errors='replace'), newline=None)
			contacts = get_csv_contacts(_file)
			if type(contacts) == str:
				error = contacts
			else:
				import_contacts(contacts)
				return redirect(reverse('friends', args=['clients']))
		else:
			error = 'Not a csv file'
	return render_to_response('contacts_hs/import_csv_contacts.html', {
			'error': error,
		},
		context_instance=RequestContext(request))


# @user_authenticated
# def import_contacts_status(request, base_template_name="messages/base.html"):
# 	is_floatbox = request.GET.get('fb', False)
# 	google_oauth = False
# 	facebook_auth = False
# 	if is_floatbox:
# 		base_template_name = "base_floatbox.html"
# 		try:
# 			google_contacts = GoogleContacts(request.user)
# 		except oauth2client.client.Error:
# 			google_oauth = True
# 	try:
# 		ua = UserAssociation.objects.get(user=request.user, service='facebook')
# 		load_facebook_user_data(ua.token) # to check access
# 	except (FacebookAuthError, UserAssociation.DoesNotExist):
# 		facebook_auth = True
#
# 	import_status_list = ContactsImportStatus.objects.filter(user=request.user)
# 	is_running = False
# 	for import_status in import_status_list:
# 		if not import_status.is_running():
# 			import_status.delete()
# 		else:
# 			is_running = True
#
# 	request.session['oauth_callback_redirect'] = reverse('oauth_window_close')
# 	c = {'import_status_list': import_status_list,
# 		 'is_running': is_running,
# 		 'base_template_name': base_template_name,
# 		 'google_oauth': google_oauth,
# 		 'facebook_auth': facebook_auth,
# 		 'is_floatbox': int(is_floatbox)}
# 	return direct_to_template(request, "friends_app/import_contacts.html", c)

class ImportContactsStatus(TemplateView):
	template_name = "friends_app/import_contacts.html"
	base_template_name = "django_messages/base.html"
	google_oauth = False
	facebook_auth = False

	def get_context_data(self, **kwargs):
		context = super(ImportContactsStatus, self).get_context_data(**kwargs)
		is_floatbox = self.request.GET.get('fb', False)
		google_oauth = False
		facebook_auth = False
		if is_floatbox:
			self.base_template_name = "base_floatbox.html"
			try:
				GoogleContacts(self.request.user)
			except oauth2client.client.Error:
				self.google_oauth = True
		try:
			ua = UserAssociation.objects.get(user=self.request.user, service='facebook')
			load_facebook_user_data(ua.token)  # to check access
		except (FacebookAuthError, UserAssociation.DoesNotExist):
			self.facebook_auth = True

		import_status_list = ContactsImportStatus.objects.filter(user=self.request.user)
		is_running = False
		for import_status in import_status_list:
			if not import_status.is_running():
				import_status.delete()
			else:
				is_running = True

		self.request.session['oauth_callback_redirect'] = reverse('oauth_window_close')
		context.update({
			'import_status_list': import_status_list,
			'is_running': is_running,
			'base_template_name': self.base_template_name,
			'google_oauth': google_oauth,
			'facebook_auth': facebook_auth,
			'is_floatbox': int(is_floatbox)
		})
		return context

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(ImportContactsStatus, self).dispatch(request, *args, **kwargs)


@user_authenticated
def delete_contact(request, contact_id, redirect):
	try:
		Contact.objects.get(id=contact_id).delete()
	except Contact.DoesNotExist:
		raise Http404

	if redirect == 'referrals':
		return friends(request, 'referrals')
	else:
		return friends(request, 'clients')


class CheckImportStatus(UserLoggedIn):
	def post(self, request, format=None):
		try:
			import_status = ContactsImportStatus.objects.get(user=request.user)
			result = {'status': import_status.status,
				'message': import_status.message()}
			if not import_status.is_running():
				import_status.delete()

			return Response(result)
		except ContactsImportStatus.DoesNotExist:
			return Response('')
