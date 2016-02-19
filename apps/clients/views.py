from datetime import timedelta

from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseNotFound, HttpResponse, Http404,
	HttpResponseBadRequest, QueryDict)
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template.loader import render_to_string

from pinax.apps.account.views import password_reset as pinax_password_reset
from pinax.apps.account.forms import AddEmailForm
from emailconfirmation.models import EmailAddress, EmailConfirmation
from mezzanine.blog.models import BlogPost
from django_yubin.models import Log
from django_yubin.constants import RESULT_SENT
from avatar.models import Avatar

from rest_framework.response import Response
from rest_framework.views import APIView

from contacts_hs.models import ContactInfo
from payments.utils import get_user_customer
from healers.models import (Appointment, Clients, Healer, is_my_client,
	is_healer, is_wellness_center, Referrals)
from healers.views import healer
from healers.utils import (friend_bar_processor, check_center_permissions,
							get_healer_info_context, send_hs_mail, get_healer)
from account_hs.views import UserAuthenticated
from account_hs.exceptions import ResetPasswordSeveralEmailsNotVerified
from account_hs.models import EmailConfirmationExpiredError
from account_hs.authentication import user_authenticated
from account_hs.forms import ResetPasswordFormHS
from account_hs.utils import login_user, get_or_create_email_address
from account_hs.views import get_embed_params, PLUGIN_KEY

from clients.models import (Client, ClientPhoneNumber, ClientVideo,
	SiteJoinInvitation, ReferralsSent, Gallery, ClientLocation)
from clients.forms import (VideoForm, UploadedVideosImportForm,
	ClientForm, PhoneForm, ContactInfoForm, ClientLocationForm,
	SendReferralForm)
from healers.ajax import convert_timestamp


@user_authenticated
def appointments(request, template_name="clients/appointments.html"):
	get_object_or_404(Client, user__id=request.user.id)
	now = settings.GET_NOW()
	end = now + timedelta(days=180)

	appts = Appointment.objects.filter(client__user__id=request.user.id)
	appts = appts.filter_by_date(now - timedelta(days=1)).order_by('start_date', 'start_time')
	appts = Appointment.generate_recurrency(appts, now, end)

	have_unconfirmed_appts = False
	for a in appts:
		if not a.confirmed:
			have_unconfirmed_appts = True
			break

	posts = BlogPost.objects.published().order_by('?')[:10]
	videos = ClientVideo.objects.all().order_by('?')[:10]

	return render_to_response(template_name, {
		'appointment_list': appts,
		'user': request.user,
		'have_unconfirmed_appts': have_unconfirmed_appts,
		'posts': posts,
		'videos': videos,
		}, context_instance=RequestContext(request))


@user_authenticated
def appointment_cancel(request, appt_id, **kwargs):
	appt = get_object_or_404(Appointment, id=appt_id)

	if(request.user.id != appt.client.user.id):
		return HttpResponseNotFound("You're Not Allowed to Cancel Appointments for Another Client")

	start = request.GET.get('start', None)

	if start:
		appt, canceled_appt = appt.cancel_single(convert_timestamp(int(start)))
	else:
		appt.cancel(request.user)
		canceled_appt = appt

	canceled_appt.notify_canceled(request.user)

	action = kwargs.pop('action', None)
	if action == 'reschedule':
		return redirect(healer, appt.healer.username())
	else:
		return redirect(appointments)


@user_authenticated
def client(request, username, template_name="clients/clients_profile.html"):
	client = get_object_or_404(Client, user__username__iexact=username)

	healer = is_healer(client)
	if healer:
		return redirect(healer.healer_profile_url())

	contact_info = None
	if is_healer(request.user):
		try:
			contact_info = ContactInfo.objects.get(healer__user=request.user, client=client)
		except ContactInfo.DoesNotExist:
			pass

	is_profile_visible = Clients.objects.are_friends(request.user, client.user)

	request.friend_type = "clients"
	request.other_user = client.user
	return render_to_response(template_name, {
		"is_profile_visible": is_profile_visible,
		"phone_numbers": client.phone_numbers.all(),
		"is_me": client.user == request.user,
		"contact_info": contact_info,
#		"other_user": other_user,
	}, context_instance=RequestContext(request, {}, [friend_bar_processor]))


@user_authenticated
def profile_edit(request, template_name="clients/clients_profile_edit.html"):
	client = get_object_or_404(Client, user__id=request.user.id)
	try:
		get_user_customer(request.user)  # initiate customer
	except:
		pass
	if is_healer(client):
		return redirect('healer_edit')

	phones = ClientPhoneNumber.objects.filter(client=client)

	if request.method == 'POST':
		form = ClientForm(request.POST)
		if form.is_valid():
			if phones:
				phones[0].number = form.cleaned_data['phone']
				phones[0].save()
			else:
				ClientPhoneNumber.objects.create(client=client, number=form.cleaned_data['phone'])

			client.user.first_name = form.cleaned_data['first_name']
			client.user.last_name = form.cleaned_data['last_name']
			client.user.save()

			client.about = form.cleaned_data['about']
			client.send_reminders = form.cleaned_data['send_reminders']
			client.ghp_notification_frequency = form.cleaned_data['ghp_notification_frequency']

#			client.beta_tester = form.cleaned_data['beta_tester']
			client.save()
			return redirect('clients_profile')
	else:
		form = ClientForm(initial={
			'first_name': client.user.first_name,
			'last_name': client.user.last_name,
			'about': client.about,
			'phone': (phones[0].number if (len(phones) > 0) else ''),
			'send_reminders': client.send_reminders,
			'ghp_notification_frequency': client.ghp_notification_frequency
#			'beta_tester' : client.beta_tester
			})

	return render_to_response(template_name, {
		'client': client,
		'form': form,
		'locations': client.get_locations_objects(),
		'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
	}, context_instance=RequestContext(request))


@user_authenticated
def disable_reminders(request):
	client = request.user.client
	client.send_reminders = False
	client.save()

	return render_to_response('clients/disable_reminders.html', context_instance=RequestContext(request))


@user_authenticated
def phones(request, **kwargs):
	client = request.user.client

	form_class = kwargs.pop("form_class", PhoneForm)
	template_name = kwargs.pop("template_name", "clients/phones_edit.html")

	if request.method == "POST":
		if request.POST["action"] == "add":
			phone_form = form_class(request.POST)
			if phone_form.is_valid():
				phone_form.save(client)
				phone_form = form_class()
		else:
			phone_form = form_class()
			if request.POST["action"] == "remove":
				phone_id = request.POST["phone_id"]
				try:
					phone = ClientPhoneNumber.objects.get(
						id=phone_id,
						client=client,
					)
					phone.delete()
				except EmailAddress.DoesNotExist:
					pass
	else:
		phone_form = form_class()

	return render_to_response(template_name, {
		'client': client,
		'phone_form': phone_form,
	}, context_instance=RequestContext(request))


def select_account_type(request, service):
	if 'token' in request.session:
		token = request.session.get('token')
	else:
		return redirect('signup')

	embed = None
	if PLUGIN_KEY in request.session:
		embed = get_embed_params(request.session.pop(PLUGIN_KEY))

	ctx = {
		'token': token,
		'facebook_signup': True,
		'embed': embed
	}

	return render_to_response('account/select_type.html', RequestContext(request, ctx))


def oauth_error(request):
	error_message = request.session.pop('oauth_error_message', '')
	oauth_error_is_facebook_duplicate = request.session.pop('oauth_error_is_facebook_duplicate', False)
	ctx = {'error_message': error_message, 'oauth_error_is_facebook_duplicate': oauth_error_is_facebook_duplicate}
	return render_to_response("account/oauth_error.html", RequestContext(request, ctx))


@user_authenticated
def oauth_window_close(request):
	return render_to_response('account/oauth_window_close.html')


@user_authenticated
def location_detail(request, appointment_id):
	try:
		appt = Appointment.objects.get(id=appointment_id)
	except Appointment.DoesNotExist:
		return HttpResponse("<h3>Oops!</h3>Sorry, couldn't find that Location")

	if (appt.client.user != request.user and appt.healer.user != request.user) or \
		appt.location.addressVisibility == Healer.VISIBLE_DISABLED:

		return HttpResponse("<h3>Oops!</h3>Sorry you dont have permission to see details for this location")

	return HttpResponse("<h3>" + appt.location.title + "</h3>" +
						appt.location.address_text("<br />") +
						"<p>" + appt.location.gmaps_link("show map &raquo;") + "</p>")


@user_authenticated
def client_detail(request, client_username):
	try:
		client = Client.objects.get(user__username__iexact=client_username)
	except Client.DoesNotExist:
		return HttpResponse("<h3>Oops!</h3>Sorry, couldn't find that Client")

	client_info = client.contact_info(separator='<br />', email_link=True)
	if request.user != client.user and not is_my_client(request.user, client.user):
		client_info = None

	contact_info = client.get_contact_info(request.user.client)
	contact_info_text = None
	if contact_info:
		contact_info_text = contact_info.text(separator='<br />', email_link=True)

	healer_link = None
	healer = is_healer(client)
	logged_in_healer = Healer.objects.get(user=request.user)
	if healer:
		healer_link = healer.healer_profile_url()

	c = {
		'has_intake_form': logged_in_healer.has_intake_form(),
		'client': client,
		'user': request.user,
		'client_info': client_info,
		'contact_info': contact_info,
		'contact_info_text': contact_info_text,
		'healer_link': healer_link,
		'answered_intake_form': client.answered_intake_form(is_healer(request.user)),
	}
	return render_to_response('clients/client_detail.html', c, context_instance=RequestContext(request))


@user_authenticated
def contact_form(request, client_username):
	try:
		client = Client.objects.get(user__username__iexact=client_username)
	except Client.DoesNotExist:
		return HttpResponse("<h3>Oops!</h3>Sorry, couldn't find that Client")

	contact_info = client.get_contact_info(request.user.client)
	if not contact_info:
		contact_info = ContactInfo.objects.create(client=client,
			healer=request.user.client.healer,
			first_name=client.user.first_name,
			last_name=client.user.last_name)

	form = ContactInfoForm(request.POST or None, contact_info=contact_info)
	if form.is_valid():
		form.save()
		# if client email was not set when the client was created, do so now and
		# send invite or if a client hasn't accepted invite yet, change email
		# and send a new one.
		if (not client.user.email or
				(client.user.email != form.cleaned_data['email'] and
					not client.user.is_active)):
			client.user.email = form.cleaned_data['email']
			client.user.save()

			SiteJoinInvitation.objects.send_invitation(
				request.user, client.user.email,
				to_name='%s %s' % (client.user.first_name, client.user.last_name))

		if not client.user.is_active:
			client.user.first_name = form.cleaned_data['first_name']
			client.user.last_name = form.cleaned_data['last_name']
			client.user.save()

		return redirect('client_detail', client_username)

	c = {
		'contact_form': form,
		'contact': contact_info,
		'client_name': str(client)
	}
	return render_to_response('clients/contact_form.html', c, context_instance=RequestContext(request))


@user_authenticated
def email(request, username=None, **kwargs):
	if username and is_wellness_center(request.user):
		provider = get_healer(request.user, username)
		user = provider.user
	else:
		user = request.user

	form_class = kwargs.pop("form_class", AddEmailForm)
	template_name = kwargs.pop("template_name", "account/email.html")

	if request.method == "POST" and request.user.is_authenticated():
		if request.POST["action"] == "add":
			add_email_form = form_class(user, request.POST)
			if add_email_form.is_valid():
				add_email_form.save()
				add_email_form = form_class()  # @@@
		else:
			add_email_form = form_class()
			if request.POST["action"] == "send":
				email = request.POST["email"]
				try:
					email_address = EmailAddress.objects.get(
						user=user,
						email__iexact=email,
					)
					EmailConfirmation.objects.send_confirmation(email_address)
				except EmailAddress.DoesNotExist:
					pass
			elif request.POST["action"] == "remove":
				email = request.POST["email"]
				try:
					email_address = EmailAddress.objects.get(
						user=user,
						email__iexact=email
					)
					email_address.delete()
				except EmailAddress.DoesNotExist:
					pass
			elif request.POST["action"] == "primary":
				email = request.POST["email"]
				email_address = EmailAddress.objects.get(
					user=user,
					email__iexact=email,
				)
				email_address.set_as_primary()
	else:
		add_email_form = form_class()
	ctx = {
		"add_email_form": add_email_form,
		"edit_user": user,
		"username": username
	}

	return render_to_response(template_name, RequestContext(request, ctx))


def videos_list(request, username=None):
	videos = ClientVideo.objects.filter(videotype=ClientVideo.VIDEO_TYPE_CLIENT).order_by('?')
	#videos = ClientVideo.objects.all().order_by('-date_added')
	client = None
	if username is not None:
		client = get_object_or_404(Client, user__username__iexact=username.lower())
		videos = videos.filter(client=client)

	c = {
		'videos': videos,
		'client': client
	}
	return render_to_response('clients/videos_list.html', c,
								context_instance=RequestContext(request))


@user_authenticated
def videos(request):
	client = request.user.client
	form = VideoForm(request.POST or None, initial={'videotype': ClientVideo.VIDEO_TYPE_CLIENT})
	if form.is_valid():
		form.save(client)
		return redirect('videos')

	c = {'videos': client.videos.filter(videotype=ClientVideo.VIDEO_TYPE_CLIENT),
		'form': form}
	return render_to_response('clients/videos.html', c, context_instance=RequestContext(request))


@user_authenticated
def gallery_order(request):
	gallery_id = request.POST.get('gallery_id', None)
	order = request.POST.get('order', None)
	gallery = Gallery.objects.get(id=gallery_id)
	user = gallery.client.user
	check_center_permissions(request.user, user)
	gallery.change_order(order)
	return redirect(reverse('avatar_change', args=[user.username]))


@user_authenticated
def gallery_remove(request, id):
	gallery = get_object_or_404(Gallery, id=id)
	user = gallery.client.user
	check_center_permissions(request.user, user)
	gallery.delete()
	return redirect(reverse('avatar_change', args=[user.username]))


@login_required
def gallery_rotate(request, id, direction):
	gallery = get_object_or_404(Gallery, id=id)
	user = gallery.client.user
	check_center_permissions(request.user, user)
	gallery.rotate(direction)
	setup_url = reverse('provider_setup', args=[4])
	if setup_url in request.META.get('HTTP_REFERER', []):
		return redirect(setup_url)
	return redirect('avatar_change', user.username)


@user_authenticated
def videos_import(request):
	client = request.user.client
	form = UploadedVideosImportForm(request.POST or None)
	if form.is_valid():
		form.save(client)
		return redirect('videos')

	c = {'form': form}
	return render_to_response('clients/videos_import.html', c, context_instance=RequestContext(request))


@user_authenticated
def video_remove(request, video_id):
	client = request.user.client
	video = get_object_or_404(ClientVideo, client=client, id=video_id)
	#videotype = video.videotype
	video.delete()
	#return video_redirect_page(videotype)
	return redirect('videos')


def confirm_email(request, confirmation_key):
	confirmation_key = confirmation_key.lower()
	email_address = None
	confirmation = None
	try:
		email_address = EmailConfirmation.objects.confirm_email(confirmation_key)
	except EmailConfirmationExpiredError as e:
		confirmation = e.confirmation

	if not email_address:
		return render_to_response("emailconfirmation/confirm_email.html", {
			"email_address": email_address,
			"confirmation": confirmation
		}, context_instance=RequestContext(request))

	login_user(request, email_address.user)
	if 'next' in request.GET:
		return redirect(request.GET['next'])

	return redirect('what_next')


def resend_confirmation(request, confirmation_key=None, username=None):
	""" Resend confirmation email. If confirmation_key is None,
	send it to logged in user."""

	if confirmation_key is None:
		if username is not None:
			if is_wellness_center(request.user):
				provider = get_healer(request.user, username)
				user = provider.user
			else:
				raise Http404
		else:
			user = request.user
		if not user or user.is_anonymous():
			raise Http404
		email_address = get_or_create_email_address(user)
	else:
		confirmation = get_object_or_404(
			EmailConfirmation,
			confirmation_key=confirmation_key
		)
		email_address = confirmation.email_address

	EmailConfirmation.objects.send_confirmation(email_address)

	if username is not None:
		return redirect('friends', 'providers')
	return render_to_response(
		'account/signup_thanks.html',
		{'email': email_address.email},
		context_instance=RequestContext(request))


def password_reset(request):
	try:
		kwargs = {}
		kwargs['form_class'] = ResetPasswordFormHS
		response = pinax_password_reset(request, **kwargs)
	except ResetPasswordSeveralEmailsNotVerified:
		return redirect('login_page')
	return response


@user_authenticated
def messagelog(request, failures=False):
	if not request.user.is_superuser:
		raise Http404

	if failures:
		ctx = {'messages': Log.objects.exclude(result=RESULT_SENT)}
	else:
		ctx = {'messages': Log.objects.all()}

	return render_to_response(
		'clients/messagelog.html',
		ctx,
		context_instance=RequestContext(request))


@user_authenticated
def refer_dlg(request, username, client_or_healer):
	user = get_object_or_404(User, username__iexact=username)

	client_or_healer_val = (ReferralsSent.PROVIDER_TO_CLIENT if client_or_healer == 'client' else ReferralsSent.CLIENT_TO_PROVIDER)
	last_referral = ReferralsSent.objects.filter(referring_user=request.user,
		type=client_or_healer_val)[:1]

	message = ''
	if last_referral:
		message = last_referral[0].message

	return render_to_response('clients/referral_dlg.html', {
								'to_user': user,
								'message': message,
								'client_or_healer': client_or_healer,
								'client_or_healer_val': client_or_healer_val,
								# 'check_client':is_my_client(request.user,user)
	}, context_instance=RequestContext(request))


@user_authenticated
def location_edit(request, location_id):
	client = request.user.client
	client_location = get_object_or_404(ClientLocation, client=client, location__id=location_id)

	form = ClientLocationForm(request.POST or None, instance=client_location.location)
	if form.is_valid():
		form.save()

	return render_to_response('healers/settings/location_edit_single_page.html', {
		'form': form,
		'location': client_location.location,
		}, context_instance=RequestContext(request))


@user_authenticated
def save_ghp_notification_frequency_setting(request, frequency):
	client = get_object_or_404(Client, user=request.user)
	client.ghp_notification_frequency = frequency
	client.save()
	return redirect('clients_profile')


class GallerySetVisibility(UserAuthenticated):
	def post(self, request, id, format=None):
		try:
			is_hidden = request.POST['is_hidden']
		except:
			return HttpResponseBadRequest()

		gallery = get_object_or_404(Gallery, id=id)
		user = gallery.client.user
		check_center_permissions(request.user, user)
		gallery.hidden = is_hidden
		gallery.save()
		return Response()


class SendReferral(APIView):
	def post(self, request, format=None):
		try:
			data = request.POST['data'].encode('utf-8')
		except:
			return HttpResponseBadRequest()

		form = SendReferralForm(QueryDict(data))

		if not form.is_valid():
			errors = []
			for error in form.errors:
				css_class = '#referral_form #referral_%s'
				errors.append(css_class % error)
			return Response({'errors': errors})

		client_or_healer = form.cleaned_data['client_or_healer']
		from_user = get_object_or_404(User, username__iexact=form.cleaned_data['from_username'])
		to_user = form.cleaned_data['to_user']

		if client_or_healer == ReferralsSent.PROVIDER_TO_CLIENT:
			provider = from_user
			client = to_user
		else:
			provider = to_user
			client = from_user

		is_referral_sent = ReferralsSent.objects.filter(
			provider_user=provider,
			client_user=client,
			referring_user=request.user).count()

		if is_my_client(provider, client):
			message = "%s was already a client of %s." % (client.client, provider.client)

		elif is_referral_sent:
			message = "You already referred %s to %s before." % (client.client, provider.client)

		else:
			mail_message = form.cleaned_data['message']

			ReferralsSent.objects.create(
				referring_user=request.user,
				provider_user=provider,
				client_user=client,
				message=mail_message
			)

			if client_or_healer == ReferralsSent.CLIENT_TO_PROVIDER:
				ctx = {
					"SITE_NAME": settings.SITE_NAME,
					"client": client,
					"client_info":	client.client.contact_info(),
					"referer": request.user,
					"mail_message": mail_message
				}
				subject = render_to_string("friends/refer_client_to_provider_subject.txt", ctx)
				send_hs_mail(subject,
					"friends/refer_client_to_provider_message.txt",
					ctx,
					settings.DEFAULT_FROM_EMAIL,
					[provider.email]
					)

				if not Referrals.objects.refers_to(provider, client):
					Clients.objects.filter(from_user=request.user, to_user=provider).delete()
					if not Referrals.objects.filter(from_user=request.user, to_user=provider).exists():
						friendship = Referrals.objects.create(from_user=request.user, to_user=provider)
						friendship.save()
			else:
				provider_profile = provider.client.healer
				friendship, is_profile_visible, ctx = get_healer_info_context(provider_profile, request)
				ctx["info_only"] = True

				ctx.update({
					"SITE_NAME": settings.SITE_NAME,
					"STATIC_URL": settings.STATIC_URL,
					"provider": provider_profile,
					"referer": request.user,
					"mail_message": mail_message
				})
				subject = render_to_string("friends/refer_provider_to_client_subject.txt", ctx)
				send_hs_mail(subject,
					"friends/refer_provider_to_client_message.txt",
					ctx,
					settings.DEFAULT_FROM_EMAIL,
					[client.email],
					html_template_name="friends/refer_provider_to_client_message.html"
					)

			#update refers model

			message = "You refered %s to %s." % (client.client, provider.client)

		return Response(message)
