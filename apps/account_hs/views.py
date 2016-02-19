import json
from datetime import time

# from django.contrib import messages
# from django.utils.translation import ugettext
from django.contrib.auth.models import User
from django.contrib.auth import logout as user_logout
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseBadRequest, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.conf import settings


# from pinax.apps.account.utils import user_display
from captcha import conf
from captcha.models import CaptchaStore
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from emailconfirmation.models import EmailAddress, EmailConfirmation
from oauth_access.access import OAuth20Token, OAuthAccess
from pinax.apps.account.views import logout

from util import get_errors
from phonegap.utils import render_page
from contacts_hs.models import ContactInfo, ContactPhone, ContactEmail
from healers.utils import (invite_or_create_client_friendship, send_hs_mail,
							get_timeslot_object)
from healers.models import HealerTimeslot, WellnessCenter, Healer
from healers.forms import NewUserFormUnregistered, BookingLoginForm
from healers.threads import run_in_thread
from clients.models import ClientPhoneNumber, create_dummy_user, Client
from ambassador.settings import COOKIE_NAME as AMBASSADOR_COOKIE_NAME
import ambassador
from payments.utils import get_user_customer, get_current_subscription

from account_hs.forms import (
	HealerSignupForm, ClientSignupForm, ClientSignupNoNameForm,
	WellnessCenterSignupForm)
from account_hs.utils import (login_user, set_signup_source, after_signup,
								post_signup_processing,
								get_or_create_email_address)
from account_hs.authentication import IsActiveUser

PLUGIN_KEY = 'plugin'


def get_embed_params(username, with_name=True):
	"""
	Prepare embed params for embed views
	"""
	embed = {}
	embed['username'] = username
	client = ambassador.views.check_ambassador_program(embed['username'])
	embed['background_color'] = client.embed_background_color
	if with_name and client.is_referrals_group():
		embed['name'] = unicode(client)
	return embed


class UpdateLinkSource(APIView):
	def post(self, request, format=None):
		try:
			email = request.POST['email']
			link_source = request.POST['link_source']
		except:
			return HttpResponseBadRequest()

		try:
			healer_user = User.objects.get(email__iexact=email)
		except Exception:
			raise Http404

		client = get_object_or_404(Client, user=healer_user)
		client.link_source = link_source
		try:
			client.full_clean()
			client.save()
		except ValidationError:
			pass

		return Response()


def render_signup(extra_context={}, request=None, template=None, plugin=False,
					phonegap=False):
	embed = None
	if plugin and request:
		# for select_account_type after facebook signup
		request.session[PLUGIN_KEY] = request.COOKIES.get(AMBASSADOR_COOKIE_NAME)
		embed = get_embed_params(
			request.COOKIES.get(AMBASSADOR_COOKIE_NAME, None),
			with_name=True)

	if template is None:
		template = 'account/signup.html'

	centers = WellnessCenter.objects.filter(user__is_active=True)
	if phonegap:
		number_of_centers = 118
		number_of_healers = 1271
	else:
		number_of_centers = centers.count()
		number_of_healers = Healer.objects.filter(
			user__is_active=True).exclude(pk__in=centers).count()

	ctx = {
		'client_signup_form': ClientSignupForm(),
		'embed': embed,
		'number_of_healers': number_of_healers,
		'number_of_centers': number_of_centers
	}
	return render_page(request, template, ctx, extra_context)


def signup(request, template=None, plugin=False):
	return render_signup(request=request, template=template, plugin=plugin)


def delete(request, username=None):
	def _cancel_subscriptions():
		customer = get_user_customer(user)
		current_subscription = get_current_subscription(customer)
		for plan_type in settings.PLAN_TYPES:
			customer.cancel(plan_type)
			setattr(current_subscription, '%s_status' % plan_type, False)
			current_subscription.save()
			setattr(customer, 'payment_%s' % plan_type, 0)
			customer.save()

	if username is None:
		user = get_object_or_404(User, id=request.user.id)
	else:
		if request.user.is_superuser:
			user = get_object_or_404(User, username=username)
		else:
			raise Http404

	user.is_active = False
	user.save()
	client = user.client
	client.is_deleted = True
	client.save()

	_cancel_subscriptions()
	if username is None:
		logout(request)
		return redirect('home')
	else:
		return redirect('dashboard:delete_account')


@run_in_thread
def thread_logout(request):
	time.sleep(60)
	user_logout(request)


class SignupClient(APIView):
	def post(self, request, format=None):
		"""Find user with email if it not exists, create dummy user.
		Return empty string or string with error on error and Client on
		success."""

		def create_new_client(form, healer):
			if form.is_valid():
				user = None
				user_exist = False
				if form.cleaned_data['email']:
					try:
						user = User.objects.filter(email__iexact=form.cleaned_data['email'])[0]
						user_exist = True
					except IndexError:
						pass

				if user_exist and not user.is_active:
					error = 'This email is already in use. Please check your email and click the Email Confirmation link.'

					email_address = get_or_create_email_address(user)
					EmailConfirmation.objects.send_confirmation(email_address)
					return error

				if not user:
					user = create_dummy_user(
						form.cleaned_data['first_name'],
						form.cleaned_data['last_name'],
						form.cleaned_data['email'])

				# if can't find or create user, return None
				if not user:
					return ''

				try:
					client = Client.objects.get(user=user)
				except Client.DoesNotExist:
					client = Client(user=user)
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

				if form.cleaned_data.get('send_intake_form', False):
					#send intake form to client
					healer.send_intake_form(client)

				password = form.cleaned_data['password1']
				if password:
					client.user.set_password(password)
					client.user.save()

				EmailAddress.objects.add_email(client.user, form.cleaned_data['email'])

				after_signup(client.user, account_type='client', email_confirmed=False)

				return client

			error_list = ''
			for error in form.errors:
				if error == '__all__':
					error_list += '%s' % str(form.errors[error])
				else:
					error_list += '%s: %s' % (error, str(form.errors[error]))

			return error_list

		def get_error(error):
			challenge, response = conf.settings.get_challenge()()
			store = CaptchaStore.objects.create(challenge=challenge, response=response)
			return Response({'captcha_image': reverse('captcha-image', kwargs=dict(key=store.hashkey)),
							'captcha_code': store.hashkey, 'error': error})

		try:
			data = request.POST['data'].encode('utf-8')
		except:
			return HttpResponseBadRequest()

		qd = QueryDict(data)
		form = NewUserFormUnregistered(qd)

		timeslot = get_timeslot_object(qd['timeslot'])
		if type(timeslot) != HealerTimeslot:
			return get_error(timeslot)

		healer = timeslot.healer
		client = create_new_client(form, healer)

		if type(client) == str:
			return get_error(client)
		else:
			login_user(request, client.user)
			thread_logout(request)
			return Response(client.pk)


class Signup(APIView):
	"""Cloned from pinax.apps.account.views.signup()
	modified to work with emails that have already been verified."""

	def post(self, request, format=None):
		def get_signup_form_class():
			if signup_type == 'client':
				if no_name:
					return ClientSignupNoNameForm
				return ClientSignupForm
			elif signup_type == 'healer':
				return HealerSignupForm
			elif signup_type == 'wellness_center':
				return WellnessCenterSignupForm

		def process_form():
			"""Returns:
				user, signup_message, redirect_url."""
			user = form.save(next=request.session.pop('signup_next', ''), is_superuser=is_superuser, cookies=request.COOKIES)
			# Add to unapproved clients
			healer_username = request.session.pop('signup_healer', '')
			if healer_username:
				try:
					healer_user = User.objects.get(username__iexact=healer_username)
					invite_or_create_client_friendship(client_user=user, healer_user=healer_user, send_client_request_email=False)
				except User.DoesNotExist:
					pass

			if is_superuser:
				message = 'User %s has been successfully created.' % user.get_full_name()
				return user, message, None

			# Meant to resolve #964
			try:
				email = EmailAddress.objects.get(user=user)		# added DGL
			except EmailAddress.DoesNotExist:
				# user = User.objects.filter(first_name=form.cleaned_data["first_name"],
				# 	last_name=form.cleaned_data["last_name"]).order_by('-date_joined')[0]
				email = EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
				EmailConfirmation.objects.send_confirmation(email)

			set_signup_source(user, self.request, is_phonegap)

			# get for phonegap backward compatibility:
			post_signup_processing(user, qd.get('is_ambassador', 0) == '1', request.session)

			if settings.ACCOUNT_EMAIL_VERIFICATION and not email.verified:
				if signup_type != 'client' and not is_phonegap:
					form.login(request, user)
				return user, None, None
			else:
				form.login(request, user)
				return user, None, reverse('what_next')

		def get_url():
			if is_phonegap:
				if 'next_url' in qd:
					return qd['next_url']
				else:
					return 'signup_thanks_%s.html' % signup_type
			thanks_url = reverse('signup_thanks', args=[signup_type])
			plugin_value = qd.get(PLUGIN_KEY, False)
			if plugin_value:
				return '{}?{}={}'.format(thanks_url, PLUGIN_KEY, plugin_value)
			return thanks_url

		try:
			data = request.POST['data'].encode('utf-8')
			is_phonegap = json.loads(request.POST['is_phonegap'])
		except:
			return HttpResponseBadRequest()

		qd = QueryDict(data)
		signup_type = qd['type']
		no_name = qd.get('no_name', False)
		form_class = get_signup_form_class()

		is_superuser = qd.get('is_superuser', False)
		if is_superuser:
			if not request.user.is_superuser:
				raise Http404
		form = form_class(qd)

		if form.is_valid():
			user, thanks_message, redirect_url = process_form()
			if redirect_url is not None:
				return Response({'redirect_url': redirect_url})
			if form_class != ClientSignupForm:
				ctx_email = {
					"first_name": user.first_name,
					"last_name": user.last_name,
					"email": user.email,
					"username": user.username,
					"provider_url": ''.join([get_current_site(request).domain, '/', user.username])
				}
				send_hs_mail(
					'New Provider',
					"admin/new_provider_message.txt",
					ctx_email,
					settings.DEFAULT_FROM_EMAIL,
					settings.EMAIL_ON_SIGNUP)

			if is_superuser:
				message = render_to_string('about/thanks.html',
											{'thanks_message': thanks_message,
											'thanks_title': 'Success'})
				return Response({'message': message})

			return Response({'url': get_url(),
							'email': user.email})

		errors, error_elements, error_list_pg_bc = get_errors(form)

		return Response({'errors': errors,
						'error_elements': error_elements,
						'error_list': error_list_pg_bc})  # error_list_pg_bc for pg backward compatibility


def render_signup_thanks(extra_context, type, email_verification=True, request=None, phonegap=False):
	embed = None
	if request and PLUGIN_KEY in request.GET:
		embed = get_embed_params(request.GET[PLUGIN_KEY])

	def get_message():
		if email_verification:
			return render_to_string('account/verification_sent_message.html', {
				'phonegap': phonegap,
				'embed': embed
			})

	template = 'account/signup_thanks.html'
	ctx = {'thanks_message': get_message(),
		'embed': embed,
		'type': type}
	return render_page(request, template, ctx, extra_context)


def signup_thanks(request, type, email_verification=True):
	def get_tracking_code():
		tracking_code = settings.TRACKING_CODES[type]
		session_tracking_code = request.session.get('tracking_code', False)
		if session_tracking_code:
			tracking_code.update(session_tracking_code)
			request.session.pop('tracking_code')
		return tracking_code

	# set session to expire earlier for users with unconfirmed emails
	if email_verification:
		request.session.set_expiry(7200)  # 2 hours - 2 * 60 * 60

	ctx = {'tracking_code': get_tracking_code()}
	return render_signup_thanks(ctx, type, email_verification, request)


class Login(APIView):
	def post(self, request, format=None):
		try:
			data = request.POST['data'].encode('utf-8')
		except:
			return HttpResponseBadRequest()

		qd = QueryDict(data)
		form = BookingLoginForm(qd)
		if form.is_valid():
			form.login(request)
			thread_logout(request)
			client = Client.objects.get_or_create(user=form.user)[0]
			result = client.pk
		else:
			error_list = ''
			for error in form.errors:
				if error != '__all__':
					error_list += ('<li>%s</li>' % error)

			error_msg = ''
			if error_list:
				error_msg = 'The following fields have errors: <ul>%s</ul>' % error_list
			for error in form.non_field_errors():
				error_msg += '%s<br/>' % error

			result = error_msg

		return Response(result)


class FacebookSignup(APIView):
	def post(self, request, format=None):
		def get_data_values():
			data = request.POST['data']
			qd = QueryDict(data)
			signup_type = qd['type']

			# get for phonegap backward compatibility:
			is_ambassador = qd.get('is_ambassador', 0) == '1'
			return signup_type, is_ambassador, qd.get(PLUGIN_KEY, False)

		def process_signup():
			access = OAuthAccess('facebook')
			return access.callback(
				request,
				access,
				token,
				signup_type,
				True,
				True,
				is_ambassador,
				is_phonegap,
			)

		try:
			token = OAuth20Token(request.POST['token'])
			signup_type, is_ambassador, plugin_value = get_data_values()
			is_phonegap = json.loads(request.POST['is_phonegap'])
		except:
			return HttpResponseBadRequest()

		error = process_signup()[1]
		response = {'error': error}
		if not is_phonegap:
			response['url'] = reverse('signup_thanks_no_verification', args=[signup_type])
			if plugin_value:
				response['url'] = '{}?{}={}'.format(
					response['url'], PLUGIN_KEY, plugin_value)
		return Response(response)


class UserLoggedIn(APIView):
	permission_classes = (IsAuthenticated, )


class UserAuthenticated(APIView):
	permission_classes = (IsAuthenticated, IsActiveUser)


class EmailPasswordAuthentication(APIView):
	def get_initial_data(self):
		self.user = self.request.user
		if not self.user.is_authenticated():
			try:
				email = getattr(self.request, self.request.method)['email']
				password = getattr(self.request, self.request.method)['password']
			except:
				return HttpResponseBadRequest()
			try:
				self.user = User.objects.get(email=email)
				if not self.user.check_password(password):
					raise Http404
			except (User.DoesNotExist, KeyError):
				raise Http404
