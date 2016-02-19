from account_hs.views import UserAuthenticated
from rest_framework.response import Response

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict

from clients.models import SiteJoinInvitation
from account_hs.authentication import user_authenticated
from account_hs.forms import HealerSignupForm, ClientSignupForm
# @@@ if made more generic these could be moved to django-friends proper
from friends_app.forms import SimpleJoinInviteRequestForm, JoinInviteRequestForm
from healers.forms import NewUserForm
from healers.models import is_healer
from healers.views import friend_process
from friends.importer import import_yahoo, import_google
from friends.models import *

from friends_app.forms import (ImportVCardForm, ContactsJoinInviteRequestForm,
	PostcardJoinInviteRequestForm)


@user_authenticated
def friends(request, template_name="friends_app/invitations.html"):
	if request.method == "POST":
		invitation_id = request.POST.get("invitation", None)
		if request.POST["action"] == "accept":
			try:
				invitation = FriendshipInvitation.objects.get(id=invitation_id)
				if invitation.to_user == request.user:
					invitation.accept()
					messages.add_message(request, messages.SUCCESS,
						ugettext("Accepted friendship request from %(from_user)s") % {
							"from_user": invitation.from_user
						}
					)
			except FriendshipInvitation.DoesNotExist:
				pass
		elif request.POST["action"] == "decline":
			try:
				invitation = FriendshipInvitation.objects.get(id=invitation_id)
				if invitation.to_user == request.user:
					invitation.decline()
					messages.add_message(request, messages.SUCCESS,
						ugettext("Declined friendship request from %(from_user)s") % {
							"from_user": invitation.from_user
						}
					)
			except FriendshipInvitation.DoesNotExist:
				pass

	invites_received = request.user.invitations_to.invitations().order_by("-sent")
	invites_sent = request.user.invitations_from.invitations().order_by("-sent")
	joins_sent = request.user.join_from.all().order_by("-sent")

	return render_to_response(template_name, {
		"invites_received": invites_received,
		"invites_sent": invites_sent,
		"joins_sent": joins_sent,
	}, context_instance=RequestContext(request))


def save_join_request_form(request, form, is_to_healer=False, is_for_review=False, is_for_ambassador=False):
	# for client always create invitation
	invite_provider_recommend = form.cleaned_data.get('invite_provider_recommend', True) if is_to_healer else True

	email_template = subject_template = body_template = None
	if type(form) in [ContactsJoinInviteRequestForm, PostcardJoinInviteRequestForm]:
		if is_for_review:
			subject_template = "friends/join_invite_review_subject.txt"
			body_template = "friends/join_invite_review_message.txt"
			email_template = "friends/invite_review_postcard_message.txt"
		else:
			# recommend message only for healer
			if is_to_healer and invite_provider_recommend:
				email_template = "friends/invite_recommend_postcard_message.txt"
			else:
				email_template = "friends/invite_postcard_message.txt"

	emails = []
	if 'emails' in form.cleaned_data:
		if type(form.cleaned_data['emails']) == unicode:
			emails.append(form.cleaned_data['emails'])
		else:
			emails.extend(form.cleaned_data['emails'])
	if 'email_list' in form.cleaned_data:
		emails.extend(form.cleaned_data['email_list'])
	if 'contacts' in form.cleaned_data:
		emails.extend(o.email for o in form.cleaned_data['contacts'])

#	if healer:
#		healer.invite_message = form.cleaned_data["message"]
#		healer.save()

	invitations = []
	email_invitation_list = []
	client_requests_list = []
	provider_requests_list = []

	existing_users = []
	if 'providers' in form.cleaned_data:
		existing_users.extend(o.user for o in form.cleaned_data['providers'])
	for email in emails:
		users = EmailAddress.objects.get_users_for(email)
		if users:
			existing_users.append(users[0])
		else:
			email_invitation_list.append(email)

	for to_user in existing_users:
		if is_to_healer and is_healer(to_user):
			friend_type = 'referrals'
			provider_requests_list.append(to_user.email)
		else:
			friend_type = 'clients'
			client_requests_list.append(to_user.email)

		friend_process(request, friend_type, to_user.id, "add")

	for email in email_invitation_list:
		invitations.append(SiteJoinInvitation.objects.send_invitation(request.user,
			email,
			form.cleaned_data["message"],
			is_to_healer = is_to_healer,
			create_friendship = invite_provider_recommend,
			html_template_name = email_template,
			subject_template = subject_template,
			body_template = body_template,
			postcard_background = form.cleaned_data.get('postcard_background', None),
			is_for_ambassador = is_for_ambassador))

	return invitations, email_invitation_list, client_requests_list, provider_requests_list


@user_authenticated
def invite(request, emails="", form_class=JoinInviteRequestForm, **kwargs):
	template_name = kwargs.get("template_name", "friends_app/invite.html")

#	if (invite_type=="provider") and not request.user.is_superuser:
#		raise Http404

	is_for_review = kwargs.get('is_for_review', False)
	is_for_ambassador = kwargs.get('is_for_ambassador', False)

	is_postcard = False
	form_types = {
		'autocomplete': ContactsJoinInviteRequestForm,
		'bulk_invite': PostcardJoinInviteRequestForm
	}
	if 'form_type' in request.POST:
		form_class = form_types.get(request.POST['form_type'], form_class)
	if form_class in form_types.values():
		is_postcard = True

	if request.is_ajax() and not 'form_type' in request.POST:
		template_name = kwargs.get(
			"template_name_facebox",
			"friends_app/invite_facebox.html"
		)

	if is_postcard and request.is_mobile:
		template_name = 'friends_app/invite_postcard_iphone.html'

	inline_postcard = request.is_ajax() and 'form_type' in request.POST

	try:
		healer = request.user.client
		form_initial = {'message': healer.invite_message}
	except Exception:
		healer = None
		form_initial = {}

	if emails:
		form_initial['emails'] = emails

	form_initial['invite_type'] = 'client'

	imported_contacts = request.session.pop('imported_contacts', None)
	join_request_form = form_class(user=request.user, imported_contacts=imported_contacts, initial=form_initial)
	email_invitation_list = []
	client_requests_list = []
	provider_requests_list = []

	invite_type = None
	if request.method == "POST":
		join_request_form = form_class(request.POST, user=request.user)
		if join_request_form.is_valid():
			invite_type = join_request_form.cleaned_data.get('invite_type', None)
			(invitations, email_invitation_list, client_requests_list, provider_requests_list) = save_join_request_form(
				request,
				join_request_form,
				invite_type=="provider",
				is_for_review=is_for_review,
				is_for_ambassador=is_for_ambassador)

			healer.invite_message = join_request_form.cleaned_data["message"]
			healer.save()

			join_request_form = form_class(user=request.user, initial={
				'message': join_request_form.cleaned_data["message"],
				'invite_type': join_request_form.cleaned_data["invite_type"]})
		elif inline_postcard:
			return HttpResponse('error')

	request.session['oauth_callback_redirect'] = reverse('import_contacts_status')
	return render_to_response(template_name, {
		"is_for_review": is_for_review,
		"is_for_ambassador": is_for_ambassador,
		"invite_type": invite_type if invite_type else kwargs.get("invite_type", "client"),
		"join_request_form": join_request_form,
		"invitation_sent_to": email_invitation_list,
		"client_requests": client_requests_list,
		"provider_requests": provider_requests_list,
		"from_inline_postcard": inline_postcard
		}, context_instance=RequestContext(request))


def accept_join(request, confirmation_key, intake_form=False):
	join_invitation = get_object_or_404(SiteJoinInvitation,
		confirmation_key=confirmation_key.lower())
	client_signup_form = None
	if request.user.is_anonymous():
		first_name = ''
		if join_invitation.contact.name:
			first_name = join_invitation.contact.name
		client_signup_form = ClientSignupForm(initial={
			'first_name': first_name,
			'email': join_invitation.contact.email,
			'confirmation_key': join_invitation.confirmation_key
		})

	return render_to_response('account/signup.html', {
		'client_signup_form': client_signup_form,
		'intake_form': intake_form,
	}, context_instance=RequestContext(request))


@user_authenticated
def contacts(request, form_class=ImportVCardForm,
		template_name="friends_app/contacts.html"):
	if request.method == "POST":
		if request.POST["action"] == "upload_vcard":
			import_vcard_form = form_class(request.POST, request.FILES)
			if import_vcard_form.is_valid():
				imported, total = import_vcard_form.save(request.user)
				messages.add_message(request, messages.SUCCESS,
					ugettext("%(total)s vCards found, %(imported)s contacts imported.") % {
						"imported": imported,
						"total": total
					}
				)
				import_vcard_form = ImportVCardForm()
		else:
			import_vcard_form = form_class()
			if request.POST["action"] == "import_yahoo":
				bbauth_token = request.session.get("bbauth_token")
				del request.session["bbauth_token"]
				if bbauth_token:
					imported, total = import_yahoo(bbauth_token, request.user)
					messages.add_message(request, messages.SUCCESS,
						ugettext("%(total)s people with email found, %(imported)s contacts imported.") % {
							"imported": imported,
							"total": total
						}
					)
			if request.POST["action"] == "import_google":
				authsub_token = request.session.get("authsub_token")
				del request.session["authsub_token"]
				if authsub_token:
					imported, total = import_google(authsub_token, request.user)
					messages.add_message(request, messages.SUCCESS,
						ugettext("%(total)s people with email found, %(imported)s contacts imported.") % {
							"imported": imported,
							"total": total
						}
					)
	else:
		import_vcard_form = form_class()

	return render_to_response(template_name, {
		"import_vcard_form": import_vcard_form,
		"bbauth_token": request.session.get("bbauth_token"),
		"authsub_token": request.session.get("authsub_token"),
	}, context_instance=RequestContext(request))


@user_authenticated
def friends_objects(request, template_name, friends_objects_function, extra_context={}):
	"""
	Display friends' objects.

	This view takes a template name and a function. The function should
	take an iterator over users and return an iterator over objects
	belonging to those users. This iterator over objects is then passed
	to the template of the given name as ``object_list``.

	The template is also passed variable defined in ``extra_context``
	which should be a dictionary of variable names to functions taking a
	request object and returning the value for that variable.
	"""

	friends = friend_set_for(request.user)

	dictionary = {
		"object_list": friends_objects_function(friends),
	}
	for name, func in extra_context.items():
		dictionary[name] = func(request)

	return render_to_response(template_name, dictionary, context_instance=RequestContext(request))


class CreateJoinInvitation(UserAuthenticated):
	""" Create join invitation. """
	def post(self, request, format=None):
		contact_id = request.POST['contact_id']
		key = request.POST['key']
		if len(key.strip()) == 0:
			return Response("Invalid key.")

		try:
			contact = Contact.objects.get(id=contact_id, user=request.user)
		except Contact.DoesNotExist:
			return Response("Could not find that contact.")

		try:
			invitation = SiteJoinInvitation.objects.get(from_user=request.user, contact=contact)
		except SiteJoinInvitation.DoesNotExist:
			invitation = SiteJoinInvitation.objects.create(from_user=request.user, contact=contact,
				message="", status="1", key=key, is_from_site=False, is_to_healer=False)

		if getattr(settings, "FACEBOOK_DEV", False):
			url = 'https://www.healersource.com'
		else:
			url = request.build_absolute_uri(invitation.accept_url())
		return Response({'url': url, 'confirmation_key': invitation.confirmation_key})


class ConfirmSentJoinInvitation(UserAuthenticated):
	""" Confirm that join invitation is sent to contact. """
	def post(self, request, format=None):
		confirmation_key = request.POST['confirmation_key']
		is_to_healer = request.POST['is_to_healer']
		try:
			invitation = SiteJoinInvitation.objects.get(confirmation_key=confirmation_key)
		except SiteJoinInvitation.DoesNotExist:
			return Response("Could not find that invitation.")

		invitation.status = "2"
		invitation.is_to_healer = is_to_healer
		invitation.save()

		return Response({'contact_id': invitation.contact.id})


class SendInvite(UserAuthenticated):
	""" Send invite to email. """
	def post(self, request, format=None):
		def create_new_client_new(form, healer, is_to_healer):
			if form.is_valid():
				user = None
				user_exist = False
				if form.cleaned_data['email']:
					try:
						user = User.objects.filter(email__iexact=form.cleaned_data['email'])[0]
						user_exist = True
					except IndexError:
						pass

				if not user:
					user = create_dummy_user(
						form.cleaned_data['first_name'],
						form.cleaned_data['last_name'],
						form.cleaned_data['email'])

				# if can't find or create user, return None
				if not user:
					return None, None

				is_client = is_my_client(healer.user, user)

				if not user_exist:
					SiteJoinInvitation.objects.send_invitation(
						healer.user,
						form.cleaned_data['email'],
						message='',
						is_to_healer=is_to_healer,
						is_from_site=False,
						to_name='%s %s' % (user.first_name, user.last_name))

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
				if form.cleaned_data['phone']:
					client.phone_numbers.add(ClientPhoneNumber(number=form.cleaned_data['phone']))
					contact_info.phone_numbers.add(ContactPhone(number=form.cleaned_data['phone']))
				if form.cleaned_data.get('referred_by', False):
					client.referred_by = form.cleaned_data['referred_by']
					client.save()

				client_entry = autocomplete_hs.views.build_client_entry(client)

				if form.cleaned_data.get('send_intake_form', False):
					#send intake form to client
					healer.send_intake_form(client)

				return client, {'status': 'success', 'client': json.dumps(client_entry)}
			else:
				error_list = ''
				error_elements = []
				for error in form.errors:
					error_elements.append('#new_user_form #id_%s' % error)
					if error == '__all__':
						error_list += '%s' % str(form.errors[error])
					else:
						error_list += '%s: %s' % (error, str(form.errors[error]))

					#	   for error in form.non_field_errors:
					#		   error_list += ('<li>%s</li>' % error)

				return None, {'status': 'fail', 'error_elements': error_elements, 'error_list': error_list}

		qd = QueryDict(request.POST['data'].encode('utf-8'))
		qd_form = QueryDict('').copy()
		form = SimpleJoinInviteRequestForm(qd)
		if form.is_valid():
			try:
				contact_id = qd.get('contact_id', -1)
				contact = Contact.objects.get(id=contact_id)
			except Contact.DoesNotExist:
				contact = None

			try:
				healer = request.user.client
				healer.invite_message = form.cleaned_data["message"]
				healer.save()
			except ObjectDoesNotExist:
				pass

			reload_page = True
			if contact:
				name_split = contact.name.partition(' ')
				qd_form['first_name'] = name_split[0]
				qd_form['last_name'] = name_split[2]
				qd_form['email'] = contact.email
				qd_form['phone'] = ''
				qd_form['referred_by'] = ''

				form = NewUserForm(qd_form)

				create_new_client_new(form, request.user.client.healer, is_to_healer=qd.get('is_to_healer', False))
			else:
				(invitations,
				email_invitation_list,
				client_requests_list,
				provider_requests_list) = save_join_request_form(request, form, is_to_healer=qd.get('is_to_healer', False))

				if not (client_requests_list or provider_requests_list):
					reload_page = False

			return Response({'reload_page': reload_page})
		else:
			error_list = ""
			error_elements = []
			for error in form.errors:
				error_elements.append('#simple_invite_form #id_%s' % error)
				error_list += ("<li>%s</li>" % error)

			return Response({'error_list': error_list, 'error_elements': error_elements})
