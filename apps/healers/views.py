import re
from xhtml2pdf import pisa
import uuid
import imghdr
import json
from copy import deepcopy
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.gis.measure import D
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User, Permission
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.utils import IntegrityError
from django.db.models.query_utils import Q
from django.http import (HttpResponseRedirect, Http404, HttpResponse,
	HttpResponseBadRequest, QueryDict)
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.http import int_to_base36
from django.views.generic import TemplateView

from rest_framework.response import Response
from rest_framework.views import APIView

from util import is_correct_image_file_type, absolute_url
from account_hs.views import UserAuthenticated
from account_hs.utils import get_or_create_email_address
from account_hs.forms import find_user
from account_hs.authentication import user_authenticated
import autocomplete_hs
from friends.models import Friendship
from friends_app.forms import ContactsJoinInviteRequestForm
from blog_hs.views import blog_import
from messages_hs.forms import ComposeFormUnregistered
from sync_hs.facebook import get_facebook_auth_url
from mezzanine.blog.models import BlogPost
from clients.forms import AboutClientForm, VideoForm, RemoteSessionsForm
from clients.models import (Client, ClientLocation, ClientPhoneNumber,
	ClientVideo, ReferralsSent, is_dummy_user, create_dummy_user,
	SiteJoinInvitation)
from clients.utils import avatar_file_path

if 'notification' in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

from avatar.models import Avatar
from avatar.forms import PrimaryAvatarForm

import payments
from payments.forms import BookingPaymentsSettingsForm
from payments.stripe_connect import create_card_token, charge
from payments.utils import get_user_customer

from contacts_hs.models import ContactInfo, ContactPhone, ContactEmail
from modality.models import Modality, ModalityCategory
from events.models import Event

from ambassador.handlers import set_ambassador

from healers.models import (Healer, WellnessCenter, Vacation, Clients,
	Referrals, Appointment, HealerTimeslot, Timeslot, LOCATION_COLOR_LIST,
	TreatmentType, TreatmentTypeLength, is_my_client, Location, Room,
	WellnessCenterTreatmentType, is_healer, check_wellness_center_provider_perm,
	is_wellness_center, wcenter_get_provider, WellnessCenterTreatmentTypeLength,
	DiscountCode, GiftCertificate)
from healers.ajax import getTimeslotsReadonly, check_schedule_permission
from healers.utils import (get_healer_info_context,
	invite_or_create_client_friendship, get_friend_classes,
	friend_processor, friend_bar_processor, send_hs_mail,
	get_imported_contacts, Setup_Step_Names, get_fill_warning_links,
	get_visible_healers_in_wcenter, get_wcenter_location_ids,
	get_healers_in_wcenter_with_schedule_editing_perm,
	get_wcenter_unconfirmed_appts, get_healer_wcenters_locations,
	wcenter_healer_has_treatment_types_, get_treatment_lengths_locations,
	get_treatments_locations_and_rooms, has_treatments, get_username,
	get_healer, get_providers, get_available_healers,
	check_center_permissions, get_treatment_length_bar_and_treatment_lengths,
	get_tts_ttls_tbar_avail_ttls, exclude_not_selected_treatment_lengths,
	create_provider_availabilities_for_timeslot, get_location, get_locations,
	add_user_to_clients, save_phone_number)
from healers.forms import (HealerForm, WellnessCenterForm, VacationForm,
	LocationForm, NewUserForm, NewUserFormUnregistered, BookingLoginForm,
	ClientsSearchForm, TreatmentTypeForm, TreatmentTypeLengthForm,
	ScheduleSettingsForm, HealerOptionalInfoForm, CreateProviderForm,
	WellnessCenterOptionalInfoForm, RoomForm, DiscountCodeForm,
	GiftCertificatesSettingForm, GiftCertificatesPurchaseForm,
	GiftCertificatesPurchaseUnregForm)


class HealerAuthenticated(UserAuthenticated):
	def get_initial_data(self):
		self.healer = get_object_or_404(Healer, user=self.request.user)


def add_stripe_connect_context(healer, context):
	context['is_deposit_required'] = healer.is_payment_or_card_required()
	if context['is_deposit_required']:
		context['STRIPE_PUBLIC_KEY'] = healer.stripe_api_key()
		context['STRIPE_APP_PUBLIC_KEY'] = settings.STRIPE_PUBLIC_KEY
	return context


def get_wcenter_treatment_types(user, wellness_center, healer=None):
	"""Get only available treatment types for center or healer in center if healer argument is set."""
	def remove_treatment_types_without_healer_availability():
		return [
			treatment_type
			for treatment_type in treatment_types
			if get_available_healers(user, wellness_center, treatment_type, healer)
		]

	treatment_types = set()
	wcenter_treatment_types = WellnessCenterTreatmentType.objects.filter(wellness_center=wellness_center)
	if healer is not None:
		wcenter_treatment_types = wcenter_treatment_types.filter(healer=healer)
	for wcenter_treatment_type in wcenter_treatment_types:
		treatment_types |= set(wcenter_treatment_type.treatment_types.filter(is_deleted=False))

	treatment_types = remove_treatment_types_without_healer_availability()
	treatment_types = sorted(treatment_types, key=lambda u: u.title)
	return treatment_types


def get_treatment_length_bar(treatment_lengths, treatment_types):
	return len(treatment_lengths) > len(treatment_types)


def add_descriptions_to_treatment_lengths(treatment_lengths):
	for tl in treatment_lengths:
		tl.description = tl.treatment_type.description
	return treatment_lengths


def wellness_center_view(request, wellness_center, location, template_name='healers/wellness_center.html'):
	def get_selected_location():
		if location is not None:
			location_object = get_location(wellness_center, location)
			if location_object is None:
				raise Http404
			return location_object

	def get_selected_location_id():
		if location_object is not None:
			return location_object.pk

	is_client, is_profile_visible, context = get_healer_info_context(wellness_center, request)

	if not is_profile_visible:
		raise Http404

	new_user_form = NewUserFormUnregistered()
	compose_form = ComposeFormUnregistered()
	login_form = BookingLoginForm()

	healers_visible = get_visible_healers_in_wcenter(request.user, wellness_center)
	is_schedule_visible = wellness_center.is_schedule_visible(request.user, is_client)
	providers_specialities = ModalityCategory.objects.filter(modality__healer__in=healers_visible).distinct('title')
	providers_modalities = Modality.objects.filter(healer__in=healers_visible).distinct('title')
	timeslot_list = getTimeslotsReadonly(request=request, healer=wellness_center)
	location_object = get_selected_location()
	treatment_types, treatment_lengths, treatment_length_bar, available_treatment_lengths = get_tts_ttls_tbar_avail_ttls(request.user, wellness_center, location=location_object)

	is_me = False
	fill_warning_links = None
	if wellness_center.user == request.user:
		is_me = True
		fill_warning_links = get_fill_warning_links(wellness_center, wcenter=wellness_center)

	context = add_stripe_connect_context(wellness_center, context)

	return render_to_response(template_name, dict({
		'is_schedule_visible': is_schedule_visible,
		'new_user_form': new_user_form,
		'compose_form': compose_form,
		'login_form': login_form,
		'locations_objects': get_locations(wellness_center, location, only_visible=True),
		'selected_location_id': get_selected_location_id(),
		'referrals_from_me': healers_visible,
		'timeslot_list': timeslot_list,
		'treatment_types': treatment_types,
		'treatment_lengths': treatment_lengths,
		'treatment_length_bar': treatment_length_bar,
		'fill_warning_links': fill_warning_links,
		'is_me': is_me,
		'first_bookable_time': wellness_center.get_first_bookable_time(),
		'appt_schedule_or_request': wellness_center.appt_schedule_or_request(context['client']),
		'providers_specialities': providers_specialities,
		'providers_modalities': providers_modalities,
		'wcenter_id': wellness_center.id,
		'events': Event.objects.current(client=wellness_center),
		'providers': get_available_healers(request.user, wellness_center),
		'available_treatment_lengths': available_treatment_lengths,
		'is_skip_provider_step': wellness_center.is_skip_provider_step(),
		}, **context), context_instance=RequestContext(request, {}, [friend_bar_processor]))


def healer(request, username, template_name="healers/healer.html",
	treatment_type=None, location=None, **kwargs):
	def get_referrals_from_me():
		referring_users = [o['friend'] for o in Referrals.objects.referrals_from(healer.user)]
		healers = Healer.complete.filter(user__in=referring_users)
		return [h.user for h in healers if h.is_visible_to(request.user)][:10]

	def filter_treatment_type():
		if treatment_type is not None:
			for tt in treatment_types:
				if tt.slug() == treatment_type:
					return [tt]
			return []
		return treatment_types.order_by('is_default').reverse()

	#TODO: !!! healer() and healer var is a bad habit !!!
	healer = get_object_or_404(Healer, user__username__iexact=username, user__is_active=True)

	if request.user.pk != healer.user.pk and treatment_type is None and location is None:
		if healer.healer_profile_url(absolute=False) != request.path:
			return redirect(healer.healer_profile_url(), permanent=True)

	wellness_center = is_wellness_center(healer)
	if wellness_center:
		return wellness_center_view(request, wellness_center, location)

	is_client, is_profile_visible, context = get_healer_info_context(healer, request)

	if not is_profile_visible and not request.user.is_superuser:
		raise Http404

	new_user_form = NewUserFormUnregistered()
	compose_form = ComposeFormUnregistered()
	login_form = BookingLoginForm()
	referrals_from_me = get_referrals_from_me()
	empty_avatars = xrange(6 - len(referrals_from_me) % 6)

	timeslot_list = getTimeslotsReadonly(request=request, healer=healer,
		only_my_locations=True)

	treatment_types = TreatmentType.objects.filter(healer=healer, is_deleted=False)
	treatment_types = filter_treatment_type()
	treatment_lengths = TreatmentTypeLength.objects.select_related().filter(treatment_type__in=treatment_types, is_deleted=False)

	treatment_length_bar, treatment_lengths = get_treatment_length_bar_and_treatment_lengths(treatment_types,
		treatment_lengths)

#	try:
#		default_treatment = treatment_lengths.filter(treatment_type__is_default=True, is_default=True)[0]
#	except IndexError:
#		default_treatment = None

	posts = BlogPost.objects.published().filter(user=healer.user).order_by('?')[:10]
	videos = ClientVideo.objects.filter(client=healer, videotype=ClientVideo.VIDEO_TYPE_CLIENT).order_by('?')[:10]

	is_me = False
	fill_warning_links = None
	if healer.user == request.user:
		is_me = True
		fill_warning_links = get_fill_warning_links(healer)

	context = add_stripe_connect_context(healer, context)

	return render_to_response(template_name, dict({
		'is_schedule_visible': healer.is_schedule_visible(request.user, is_client),
		'new_user_form': new_user_form,
		'compose_form': compose_form,
		'login_form': login_form,
		'referrals_from_me': referrals_from_me,
		'locations_objects': get_locations(healer, location, only_visible=True),
		'empty_avatars': empty_avatars,
		'timeslot_list': timeslot_list,
		'treatment_types': treatment_types,
		'treatment_lengths': treatment_lengths,
		'treatment_length_bar': treatment_length_bar,
		'fill_warning_links': fill_warning_links,
		'is_me': is_me,
		'show_edit': is_me,
		'first_bookable_time': healer.get_first_bookable_time(),
		'appt_schedule_or_request': healer.appt_schedule_or_request(context['client']),
		'posts': posts,
		'videos': videos,
		'events': Event.objects.current(client=healer),
		'editing_self': not username or (request.user.username == username),
		}, **context), context_instance=RequestContext(request, {}, [friend_bar_processor]))


@user_authenticated
def manage_discount_codes(request):
	healer = get_object_or_404(Healer, user=request.user)
	form = DiscountCodeForm(request.POST or None, healer=healer)
	if form.is_valid():
		form.save()
		form = DiscountCodeForm()
	return render_to_response('healers/manage_discount_codes.html', {
		'discount_codes': DiscountCode.objects.filter(healer=healer, is_gift_certificate=False),
		'form': form,
		}, context_instance=RequestContext(request))


@user_authenticated
def edit_discount_code(request, code_id):
	form = DiscountCodeForm(request.POST or None,
		instance=DiscountCode.objects.get(pk=code_id))
	if form.is_valid():
		form.save()
	return render_to_response('healers/edit_discount_code.html', {
		'form': form,
		}, context_instance=RequestContext(request))


@user_authenticated
def gift_certificates(request):
	# if request.user.username not in settings.GIFT_CERTIFICATES_BETA_USERS:
	# 	raise Http404

	healer = get_object_or_404(Healer, user=request.user)
	form = GiftCertificatesSettingForm(request.POST or
		{'gift_certificates': healer.gift_certificates_enabled,
		'gift_certificates_expiration_period': healer.gift_certificates_expiration_period,
		'gift_certificates_expiration_period_type': healer.gift_certificates_expiration_period_type})

	if request.method == 'POST':
		if form.is_valid():
			if healer.has_enabled_stripe_connect():
				healer.gift_certificates_enabled = form.cleaned_data['gift_certificates']
				healer.gift_certificates_expiration_period = form.cleaned_data['gift_certificates_expiration_period']
				healer.gift_certificates_expiration_period_type = form.cleaned_data['gift_certificates_expiration_period_type']
				healer.save()
	return render_to_response('healers/gift_certificates.html', {
		'form': form,
		'certificates': GiftCertificate.objects.filter(discount_code__healer=healer).select_related()
		}, context_instance=RequestContext(request))


def redeem_certificate(request, code):
	gift_certificate = get_object_or_404(GiftCertificate, discount_code__code=code)
	gift_certificate.redeem()
	return redirect('gift_certificates')


def purchase_gift_certificate(request, username):
	def create_certificate():
		def create_discount_code():
			def generate_code():
				code = str(uuid.uuid4())[:6].upper()
				if DiscountCode.objects.filter(code__iexact=code).exists():
					return generate_code()
				return code

			return DiscountCode.objects.create(healer=healer,
												code=generate_code(),
												amount=amount,
												type='$',
												remaining_uses=1,
												is_gift_certificate=True)
		discount_code = create_discount_code()
		return GiftCertificate.objects.create(purchased_for=purchased_for,
			purchased_by=purchased_by,
			discount_code=discount_code,
			message=message)

	def email_healer():
		subject = '%s has purchased a Gift Certificate from you!' % purchased_by
		send_hs_mail(subject, 'healers/emails/gift_certificate_purchased_healer.txt',
			{'certificate': certificate, 'link': gift_certificates_url},
			settings.DEFAULT_FROM_EMAIL, [healer.user.email])

	def email_buyer():
		def create_pdf():
			def convertHtmlToPdf(sourceHtml):
				def link_callback(uri, rel):
					path = uri.replace(settings.STATIC_URL, settings.STATIC_ROOT + '/')
					path = path.replace(settings.MEDIA_URL, settings.MEDIA_ROOT + '/')
					return path

				with open(filename, 'w+b') as f:
					#pisaStatus =
					pisa.CreatePDF(
							sourceHtml,
							dest=f,
							link_callback=link_callback)
				#return pisaStatus.err

			sourceHtml = render_to_string('healers/gift_certificate_pdf.html', {
				'certificate': certificate, 'healer': healer,
				'STATIC_URL': settings.STATIC_URL})
			# with open('html.html', 'w+b') as f:
			# 	f.write(sourceHtml)
			filename = '/tmp/gift_certificate_%s.pdf' % certificate.discount_code.code
			convertHtmlToPdf(sourceHtml)
			return filename

		send_hs_mail('Gift Certificate', 'healers/emails/gift_certificate_purchased_buyer.txt',
			{'certificate': certificate, 'link': gift_certificates_url},
			settings.DEFAULT_FROM_EMAIL,
			[buyer_email],
			attachment_path=create_pdf())

	def get_has_card():
		if request.user.is_authenticated():
			customer = get_user_customer(request.user)
			return customer.can_charge()
		return False

	def get_default_amount():
		for tt in healer.healer_treatment_types.all():
			for ttl in tt.lengths.all():
				cost = ttl.is_valid_cost()
				if cost:
					return int(cost)
		return 70

	healer_user = get_object_or_404(User, username=username)
	healer = get_object_or_404(Healer, user=healer_user)
	gift_certificates_url = absolute_url(reverse('gift_certificates'))
	form_initial = {'amount': get_default_amount()}
	if request.user.is_authenticated():
		if request.POST:
			form = GiftCertificatesPurchaseForm(request.POST)
		else:
			form = GiftCertificatesPurchaseForm(initial=form_initial)
	else:
		if request.POST:
			form = GiftCertificatesPurchaseUnregForm(request.POST)
		else:
			form = GiftCertificatesPurchaseUnregForm(initial=form_initial)

	certificate = None
	error = None
	has_card = get_has_card()

	if request.method == 'POST' and form.is_valid():
		amount = form.cleaned_data['amount']
		purchased_for = form.cleaned_data['purchased_for']
		message = form.cleaned_data['message']
		if request.user.is_authenticated():
			purchased_by = unicode(request.user.client)
			buyer_email = request.user.email
			customer = get_user_customer(request.user)

		else:
			purchased_by = form.cleaned_data['purchased_by']
			buyer_email = form.cleaned_data['purchased_by_email']

		if has_card:
			card_token = create_card_token(customer, healer_user)
		else:
			card_token = request.POST.get('card_token')

		certificate = create_certificate()
		charge_result = charge(card_token, healer_user, amount, certificate.description())
		if 'error' in charge_result:
			error = charge_result['error']
			certificate.delete()
			certificate.discount_code.delete()
			certificate = None
		else:
			form = None
			email_healer()
			email_buyer()

	return render_to_response('healers/gift_certificate_purchase.html',
		{'form': form, 'healer': healer, 'certificate': certificate,
		'has_card': json.dumps(has_card), 'error': error,
		'STRIPE_PUBLIC_KEY': healer.stripe_api_key()},
		context_instance=RequestContext(request))


def embed(request, username, template_name='healers/embed.html', preview=False,
		center_username=None, location=None, include_name=False):
	def get_wcenter():
		def get_center_username():
			if center_username:
				return center_username
			if is_wellness_center(healer):
				return username

		wcenter_username = get_center_username()
		if wcenter_username is not None:
			wcenter = WellnessCenter.objects.get(user__username=wcenter_username)
			# check if healer is in center. Raise 404 if not.
			get_healer(wcenter.user, username)
			return wcenter

	def get_locations():
		kwargs = {'user': request.user, 'is_client': is_client}
		if wcenter is None:
			return healer.get_locations(skip_center_locations=True, **kwargs)
		else:
			return healer.get_locations(wellness_center=wcenter, **kwargs)

	def get_embed_tts_ttls_tbar_avail_tts():
		if wcenter is None:
			tts = TreatmentType.objects.filter(healer=healer, is_deleted=False)
			ttls = TreatmentTypeLength.objects.select_related().filter(
				treatment_type__in=tts, is_deleted=False)
			treatment_type_bar, ttls = get_treatment_length_bar_and_treatment_lengths(tts, ttls)
			return tts, ttls, treatment_type_bar, ''
		else:
			if center_username is None:
				return get_tts_ttls_tbar_avail_ttls(request.user, wcenter, None, get_location(wcenter, location))
			else:
				return get_tts_ttls_tbar_avail_ttls(request.user, wcenter, healer, get_location(wcenter, location))

	def get_wcenter_id():
		if wcenter is not None:
			return wcenter.pk

	def get_stripe_connect_context():
		def get_healer():
			if wcenter is not None:
				return wcenter
			else:
				return healer
		return add_stripe_connect_context(get_healer(), {})

	def get_locations_objects():
		if wcenter is None:
			h = healer
		else:
			h = wcenter
		return h.get_locations_objects(True)

	def is_skip_provider_step():
		if wcenter:
			return wcenter.is_skip_provider_step()

	healer = get_object_or_404(Healer, user__username__iexact=username)

	client = None
	client_id = ''
	is_client = False
	try:
		client = Client.objects.get(user__id=request.user.id)
		client_id = client.id
		is_client = is_my_client(healer.user, request.user)
	except ObjectDoesNotExist:
		# empty client_id
		pass

	is_profile_visible = healer.is_visible_to(request.user, is_client)

	if not is_profile_visible:
		if request.user != healer.user:
			raise Http404

	wcenter = get_wcenter()

	locations = get_locations()
	new_user_form = NewUserFormUnregistered()
	login_form = BookingLoginForm()

	timeslot_list = getTimeslotsReadonly(request=request, healer=healer,
		only_my_locations=True)

	treatment_types, treatment_lengths, treatment_length_bar, available_treatment_lengths = get_embed_tts_ttls_tbar_avail_tts()
	request.other_user = healer.user

	return render_to_response(template_name, dict({
		#'other_user': other_user,
		'healer': healer,
		'wcenter_id': get_wcenter_id(),
		'client_id': client_id,
		'locations_objects': get_locations_objects(),
		'locations': locations,
		'new_user_form': new_user_form,
		'login_form': login_form,
		'timeslot_list': timeslot_list,
		'is_schedule_visible': healer.is_schedule_visible(request.user, is_client),
		'treatment_types': treatment_types,
		'treatment_lengths': treatment_lengths,
		'treatment_length_bar': treatment_length_bar,
		'first_bookable_time': healer.get_first_bookable_time(),
		'appt_schedule_or_request': healer.appt_schedule_or_request(client),
		'embedded_separate_center_provider_schedule': json.dumps(center_username is not None),
		'preview': preview,
		'available_treatment_lengths': available_treatment_lengths,
		'is_skip_provider_step': is_skip_provider_step(),
		'is_embedded': True,
		'compose_form': ComposeFormUnregistered(),
		'include_name': include_name}, **get_stripe_connect_context()),
			context_instance=RequestContext(request))


@user_authenticated
def add_wellness_center_permission(request, username):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	wcenter = get_object_or_404(WellnessCenter, user__username__iexact=username)

	try:
		WellnessCenter.objects.get(id=wcenter.id, healer=healer)
	except WellnessCenter.DoesNotExist:
		healer.wellness_center_permissions.add(wcenter)

		locations = wcenter.get_location_ids()
		if not HealerTimeslot.objects.filter(healer=healer, location__in=locations).exists():
			timeslots = HealerTimeslot.objects.filter(healer=wcenter)
			for tslot in timeslots:
				create_provider_availabilities_for_timeslot(wcenter, tslot, healer)

	return redirect(reverse('healer_edit', args=[healer.user.username]))


def healer_change_profile_reminder_interval(request):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	try:
		healer.profile_completeness_reminder_interval = int(request.GET['interval'])
		healer.save()
	except:
		pass #left unchanged

	return redirect('healer_edit')


@user_authenticated
def create_provider(request, template_name='healers/create_provider.html'):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	wcenter = is_wellness_center(healer)
	if not wcenter:
		raise Http404

	# check existing provider and process without form validation
	existing_user = existing_user_error = None
	if request.POST and 'email' in request.POST:
		try:
			existing_user = find_user(request.POST.get('email'))[0]
			if is_healer(existing_user):
				friend_process(request, 'referrals', existing_user.id, 'add')
				if existing_user == request.user:
					existing_user_error = \
						'%s is already being used by your Wellness Center account. Please use a different email address for this New Provider.' % existing_user.email

				# return redirect('healer_create')
		except IndexError:
			pass

	modalities = []
	form = CreateProviderForm(request.POST or None)
	if form.is_valid():
		if existing_user:
			user = existing_user
			# upgrade Client to Healer, needs data from form
			client = existing_user.client
			new_healer = Healer(
				client_ptr_id=client.id,
				about=form.cleaned_data['about'],
				years_in_practice=form.cleaned_data['years_in_practice'],
				timezone=healer.timezone)
			new_healer.__dict__.update(client.__dict__)
			new_healer.save()

			if form.cleaned_data['modalities']:
				new_healer.modality_set.add(*form.cleaned_data['modalities'][0:settings.MAX_MODALITIES_PER_HEALER])

			if not is_healer(existing_user):
				friend_process(request, 'referrals', user.id, 'add')

		else:
			user = create_dummy_user(form.cleaned_data['first_name'], form.cleaned_data['last_name'], form.cleaned_data['email'], create_real_username=True)

			get_or_create_email_address(user, email=form.cleaned_data['email'], primary=True)

			new_healer = Healer.objects.create(
				user=user,
				about=form.cleaned_data['about'],
				years_in_practice=form.cleaned_data['years_in_practice'],
				timezone=healer.timezone)
			new_healer.wellness_center_permissions.add(wcenter)

			if form.cleaned_data['phone']:
				ClientPhoneNumber.objects.create(client=new_healer, number=form.cleaned_data['phone'])

			if form.cleaned_data['modalities']:
				new_healer.modality_set.add(*form.cleaned_data['modalities'][0:settings.MAX_MODALITIES_PER_HEALER])

			friend_process(request, 'referrals', user.id, 'add')
			set_ambassador(
				client_user=new_healer.user,
				ambassador_user=request.user)

			uid = int_to_base36(user.id)
			token = default_token_generator.make_token(user)
			tour_link = request.build_absolute_uri(reverse('tour'))
			confirm_link = request.build_absolute_uri(reverse('healer_confirm',
				kwargs={'uidb36': uid, 'key': token}))

			ctx = {
				'wellness_center': str(request.user.client),
				'tour_link': tour_link,
				'confirm_link': confirm_link
			}

			subject = render_to_string('healers/emails/provider_create_subject.txt', ctx)
			send_hs_mail(subject, 'healers/emails/provider_create_message.txt', ctx, request.user.email, [user.email])

		if wcenter.payment_schedule_setting == WellnessCenter.PAYMENT_CENTER_PAYS:
			SCHEDULE_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_wcenter_schedule')
			user.user_permissions.add(SCHEDULE_PERMISSION_OBJECT)

		if existing_user:
			return redirect('friends', 'providers')
		else:
			return redirect(reverse('avatar_change', args=[user.username]) + '?next=' + reverse('friends', args=['providers']))
	else:
		#form is not valid
		# modalities = list(Modality.objects_approved.filter(id__in=[form.data['modalities']]))
		try:
			modalities = form.cleaned_data.get('modalities', [])

		except AttributeError:
			pass

	return render_to_response(template_name, {
		'healer': healer,
		'form': form,
		'modalities': modalities,
		'max_modalities': settings.MAX_MODALITIES_PER_HEALER,
	   'existing_user_error': existing_user_error,
		}, context_instance=RequestContext(request))


@login_required
def healer_edit(request, username=None,
				template_name='healers/settings/edit_profile.html'):
	editing_self = not username or (request.user.username == username)
	if editing_self:
		healer = get_object_or_404(Healer, user__id=request.user.id)
		wcenter = is_wellness_center(healer)

	else:
		# if request.user.username==username and not request.method == 'POST':
		# 	return redirect('healer_edit')
		wcenter, healer = check_wellness_center_provider_perm(request.user, username)
		if not healer:
			raise Http404

	form_class = WellnessCenterForm if wcenter and editing_self else HealerForm

	modalities = list(Modality.objects_approved.get_with_unapproved(healer).filter(healer=healer))
	modalities.reverse()

	if request.method == 'POST':
		# if not wcenter:
		# 	healer.wellness_center_permissions.clear()
		# 	wellness_centers_ids = request.POST.getlist('wellness_center')
		# 	if wellness_centers_ids:
		# 		wellness_centers = WellnessCenter.objects.get(id__in=wellness_centers_ids)
		# 		healer.wellness_center_permissions.add(wellness_centers)

		form = form_class(request.POST)
		if form.is_valid():
			save_phone_number(healer, form.cleaned_data['phone'])
			healer.user.first_name = form.cleaned_data['first_name']
			if form_class != WellnessCenterForm:
				healer.user.last_name = form.cleaned_data['last_name']
			healer.user.save()

			healer.about = form.cleaned_data['about']

			healer.profileVisibility = form.cleaned_data['profileVisibility']
			healer.client_screening = form.cleaned_data['client_screening']
			healer.send_reminders = form.cleaned_data['send_reminders']
			healer.ghp_notification_frequency = form.cleaned_data['ghp_notification_frequency']
			healer.remote_sessions = form.cleaned_data['remote_sessions']
			if form.cleaned_data['profile_completeness_reminder_interval']:
				healer.profile_completeness_reminder_interval = form.cleaned_data['profile_completeness_reminder_interval']
			healer.timezone = form.cleaned_data['timezone']

			healer.years_in_practice = form.cleaned_data['years_in_practice']

			healer.website = form.cleaned_data['website']
			healer.facebook = form.cleaned_data['facebook']
			healer.twitter = form.cleaned_data['twitter']
			healer.google_plus = form.cleaned_data['google_plus']
			healer.linkedin = form.cleaned_data['linkedin']
			healer.yelp = form.cleaned_data['yelp']

			if healer.user.is_staff:
				healer.location_bar_title = form.cleaned_data['location_bar_title']

			healer.save()
			return redirect('healer_edit', username) if username else redirect('healer_edit')
	else:
		form = form_class(initial={
			'first_name': healer.user.first_name,
			'last_name': healer.user.last_name,
			'about': healer.about,
			'phone': healer.first_phone(),
			'profileVisibility': healer.profileVisibility,
			'client_screening': healer.client_screening,
			'send_reminders': healer.send_reminders,
			'ghp_notification_frequency': healer.ghp_notification_frequency,
			'remote_sessions': healer.remote_sessions,
			'profile_completeness_reminder_interval': healer.profile_completeness_reminder_interval,
			'timezone': healer.timezone,
			'location_bar_title': healer.location_bar_title,
			'years_in_practice': healer.years_in_practice,
			'website': healer.website,
			'facebook': healer.facebook,
			'twitter': healer.twitter,
			'google_plus': healer.google_plus,
			'linkedin': healer.linkedin,
			'yelp': healer.yelp,
			})

	fill_warning_links = get_fill_warning_links(healer, modalities, wcenter, editing_self)

	referrals = [o['friend'] for o in Referrals.objects.referrals_to(request.user)]
	# wellness_centers = WellnessCenter.objects.filter(user__in=referrals)

	print '~~~~~~~~~~~~~~~~~~~~'
	print editing_self
	return render_to_response(template_name, {
		'username': username if username else healer.user.username,
		'editing_self': editing_self,
		'healer': healer,
		'fill_warning_links': fill_warning_links,
		'form': form,
		'modalities': modalities,
		'max_modalities': settings.MAX_MODALITIES_PER_HEALER,
		# 'wellness_centers': wellness_centers
		}, context_instance=RequestContext(request))


@user_authenticated
def healer_list(request, template_name='healers/healers.html', extra_context=None):
	if not request.user.is_staff:
		raise Http404

	if extra_context is None:
		extra_context = {}
	healers = Healer.objects.all().order_by('-user__username')

	client = request.user.client
	if is_healer(client):
		healers = healers.exclude(pk=client.healer)

	search_terms = request.GET.get('search', '')
	order = request.GET.get('order')
	if not order:
		order = 'name'
	if search_terms:
		healers = healers.filter(user__username__icontains=search_terms)
	if order == 'date':
		healers = healers.order_by('-date_joined')
	elif order == 'name':
		healers = healers.order_by('-user__username')
	users = [h.user for h in healers]
	return render_to_response(template_name, dict({
		'users': users,
		'order': order,
		'search_terms': search_terms,
		}, **extra_context), context_instance=RequestContext(request))


def get_all_rooms(locations, healer, is_wellnesscenter):
	location_ids = [loc['id'] for loc in locations]
	if not is_wellnesscenter:
		location_ids += get_healer_wcenters_locations(healer)
	all_rooms = Room.objects.filter(location__id__in=location_ids).order_by('name')
	return [room.as_dict() for room in all_rooms]


def get_setup_times_json(providers):
	return json.dumps({h.user.username: h.setup_time for h in providers})


@user_authenticated
def confirmed_appointments(request, year=None, month=None,
							template_name='healers/confirmed_appointments.html'):
	def filter_appontments(appointments):
		appts = appointments.filter(confirmed=True).filter_by_date(first_day, last_day)
		appts = appts.order_by('-start_date', '-start_time')
		return Appointment.generate_recurrency(appts, first_day, last_day)

	def order_treatment_lengths(treatment_lengths):
		return treatment_lengths.order_by('treatment_type', 'length')

	def get_wcenter_appts_treatment_lengths_healer_ids():
		wcenter_locations = [location['id'] for location in locations]
		treatment_lengths = {}
		healer_ids = []
		appts = filter_appontments(Appointment.objects.filter(healer__in=providers,
				location__in=wcenter_locations))
		for provider in providers:
			healer_ids.append(provider.pk)
			try:
				treatment_types = provider.wellness_center_treatment_types.get(
					wellness_center=healer.wellnesscenter).treatment_types.all().values_list('pk', flat=True)
				treatment_lengths[provider.id] = order_treatment_lengths(
					TreatmentTypeLength.objects.filter(treatment_type__in=treatment_types))
			except WellnessCenterTreatmentType.DoesNotExist:
				treatment_lengths[provider.id] = []

		return appts, treatment_lengths, healer_ids

	def get_providers_names_json():
		return json.dumps({provider.id: str(provider) for provider in providers})

	healer = get_object_or_404(Healer, user=request.user)
	local_time = healer.get_local_time()

	year = year if year else local_time.strftime('%Y')
	month = month if month else local_time.strftime('%m')

	request_month = datetime.strptime('%s-%s' % (year, month), '%Y-%m')
	current_month = local_time.replace(day=1)
	if request_month.date() < current_month.date():
		raise Http404

	locations = healer.get_locations()

	# Calculate first and last day of month, for use in a date-range lookup.
	first_day = request_month.replace(day=1)
	if first_day.month == 12:
		last_day = first_day.replace(year=first_day.year + 1, month=1)
	else:
		last_day = first_day.replace(month=first_day.month + 1)
	next_month = last_day

	# Calculate the previous month
	if first_day.month == 1:
		previous_month = first_day.replace(year=first_day.year - 1, month=12)
	else:
		previous_month = first_day.replace(month=first_day.month - 1)

	treatment_lengths = {}
	healer_ids = None
	is_wellnesscenter = is_wellness_center(healer)

	providers = get_providers(healer)

	if is_wellnesscenter:
		appts, treatment_lengths, healer_ids = get_wcenter_appts_treatment_lengths_healer_ids()
	else:
		appts = filter_appontments(Appointment.objects.filter(healer=healer))

	treatment_lengths[healer.id] = order_treatment_lengths(
			TreatmentTypeLength.objects.filter(treatment_type__healer=healer))

	treatment_lengths_locations = get_treatment_lengths_locations(healer,
		locations, treatment_lengths[healer.id])

	def get_treatment_lengths_user():
		t_lengths = set()
		treatment_lengths_ = [t_l for id, t_l in treatment_lengths_locations.items()]
		for treatment_lengths in treatment_lengths_:
			for treatment_length in treatment_lengths:
				t_lengths.add(treatment_length)
		return t_lengths

	if not is_wellnesscenter:
		treatment_lengths[healer.id] = get_treatment_lengths_user()

	treatments_rooms_json = json.dumps(get_treatments_locations_and_rooms(healer)[1])

	return render_to_response(template_name, {
		'other_user': request.user,
		'show_previous_month': request_month > current_month,
		'month': request_month,
		'next_month': next_month,
		'previous_month': previous_month,
		'repeat_choices': Appointment.REPEAT_CHOICES,
		'locations': locations,
		'locations_json': json.dumps(locations),
		'defaultTimeslotLength': healer.defaultTimeslotLength,
		'treatment_lengths': treatment_lengths,
		'appointments': appts,
		'treatment_lengths_locations': treatment_lengths_locations,
		'healer_ids': healer_ids,
		'all_rooms_json': json.dumps(get_all_rooms(locations, healer, is_wellnesscenter)),
		'treatments_rooms_json': treatments_rooms_json,
		'setup_times_json': get_setup_times_json(providers),
		'providers_names_json': get_providers_names_json(),
		}, context_instance=RequestContext(request))


@user_authenticated
def settings_view(request):
	return render_to_response('healers/settings/settings_home.html', {},
		context_instance=RequestContext(request))


@login_required
def schedule_settings(request, template_name='healers/settings/schedule.html',
		username=None, extra_context={}):
	username = get_username(request, username)
	healer = get_healer(request.user, username)

	form = ScheduleSettingsForm.create(request, healer)

	if request.POST.get('redirect'):
		return redirect(request.POST.get('redirect'))

	return render_to_response(template_name, dict({
		'form': form,
		'healer': healer,
		'username': username,
		'is_schedule_settings': True,
	}, **extra_context), context_instance=RequestContext(request))


@login_required
def payments_settings(request, template_name='payments/stripe_connect_settings.html',
		username=None, message=None, extra_context={}, redirect_to=None):
	healer = get_object_or_404(Healer, user=request.user)
	username = get_username(request, username)
	error = None
	if request.method == 'POST':
		form = BookingPaymentsSettingsForm(request.POST)
		if form.is_valid():
			user = request.user
			try:
				customer = get_user_customer(user)  # initialize customer
			except:
				error = """We're very sorry but an error has occurred setting
				up your Stripe account. Please click Save to try again."""
			if error is None:
				healer = get_object_or_404(Healer, user=user)
				healer.booking_payment_requirement = form.cleaned_data['booking_payment_requirement']
				booking_healersource_fee = int(form.cleaned_data['booking_healersource_fee'])
				if booking_healersource_fee == Healer.BOOKING_HEALERSOURCE_FEE_FIXED:
					error = payments.views.process_subscription(user, 'booking', settings.BOOKING_HEALERSOURCE_FEE)
					if error is None:
						healer.booking_healersource_fee = booking_healersource_fee
						customer.payment_booking = settings.BOOKING_HEALERSOURCE_FEE
					else:
						form = payments.views.get_booking_payments_settings_form(healer)
				else:
					payments.views.process_subscription(user, 'booking', 0)
					healer.booking_healersource_fee = booking_healersource_fee
					customer.payment_booking = 0
				customer.save()
				healer.save()
				stripe_success_redirect = request.session.pop('stripe_success_redirect', None)
				if stripe_success_redirect is not None:
					return redirect(stripe_success_redirect)
		# deposit_percentage = int(request.POST.get('deposit_percentage', 0))
		# if deposit_percentage and deposit_percentage >= 1 and deposit_percentage <= 100:
		# 	healer = Healer.objects.get(user=request.user)
		# 	healer.deposit_percentage = deposit_percentage
		# 	healer.save()
	else:
		form = payments.views.get_booking_payments_settings_form(healer)
	return render_to_response(template_name, dict({
		'form': form,
		'error': error,
		'message': message,
		'STRIPE_CONNECT_LINK': settings.STRIPE_CONNECT_LINK,
		'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
		'username': username,
	}, **extra_context), context_instance=RequestContext(request))


@user_authenticated
def payments_settings_view(request):
	return payments_settings(request)


@user_authenticated
def enable_schedule_free_trial(request):
	wc = is_wellness_center(request.user)
	if wc and wc.schedule_trial_started_date is None:
		SCHEDULE_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_wcenter_schedule')
		wc.schedule_trial_started_date = datetime.utcnow()
		wc.save()
		request.user.user_permissions.add(SCHEDULE_PERMISSION_OBJECT)
		for healer in get_healers_in_wcenter_with_schedule_editing_perm(wc):
			healer.user.user_permissions.add(SCHEDULE_PERMISSION_OBJECT)

	return redirect('schedule')


@user_authenticated
def appointment_cancel(request, appt_id):
	appt = get_object_or_404(Appointment, id=appt_id)
	check_center_permissions(request.user, appt.healer.user)
	appt.cancel(request.user)
	appt.notify_canceled(request.user, is_wellness_center(request.user), True)
	return redirect(schedule)


@user_authenticated
def schedule(request, edit_availaibility=False, username=None, location_id=None, template_name='healers/schedule.html', extra_context={}):
	def get_unconfirmed_appt_list():
		def separate_healers():
			appts = defaultdict(list)
			[appts[appt.healer.user.username].append(appt) for appt in unconfirmed_appt_list]
			return dict(appts)

		referrals = Referrals.objects.friends_for_user(request.user.id)
		clients = Clients.objects.friends_for_user(request.user.id)
		friends = clients + referrals
		friends_user_list = [f['friend'] for f in friends]
		if wcenter:
			unconfirmed_appt_list = get_wcenter_unconfirmed_appts(wcenter)
		else:
			unconfirmed_appt_list = Appointment.objects.get_active(healer).filter(confirmed=False)
			if wcenter:
				unconfirmed_appt_list = get_wcenter_unconfirmed_appts(wcenter, healer)
		unconfirmed_appt_list = unconfirmed_appt_list.order_by('healer', '-start_date', '-start_time')
		for appt in unconfirmed_appt_list:
			appt.is_my_client = appt.client.user in friends_user_list
		unconfirmed_appt_list = sorted(unconfirmed_appt_list, key=lambda k: k.is_my_client)
		return separate_healers()

	# def get_title():
	# 	if is_wellnesscenter:
	# 		return 'Schedule for ' + healer.user.get_full_name()
	# 	else:
	# 		return 'My Schedule'

	def user_has_locations():
		return requesting_healer.get_locations() != []

	def get_provider_treatments():
		def get_t_lengths(treatment_types, provider=None):
			treatment_type_lengths = TreatmentTypeLength.objects.filter(
				treatment_type__in=treatment_types)
			if provider is not None:
				treatment_type_lengths = exclude_not_selected_treatment_lengths(
					treatment_type_lengths, wcenter, provider)
			return treatment_type_lengths.order_by('treatment_type', 'length')

		provider_treatments = {}
		for provider in providers:
			treatment_types = WellnessCenterTreatmentType.objects.get_or_create(
					wellness_center=wcenter,
					healer=provider)[0].treatment_types.all()
			treatment_lengths = get_t_lengths(treatment_types, provider)
			provider_treatments[provider.user.username] = treatment_lengths

		provider_treatments[wcenter.user.username] = get_t_lengths(wcenter.healer_treatment_types.all())
		return provider_treatments

	def is_healers_schedule_not_paid():
		""" Return error text if healer's schedule is not paid and False
		otherwise."""
		wcenters = requesting_healer.get_wellness_centers()
		if wcenters:
			wcenter = wcenters[0]
			if (wcenter.payment_schedule_setting ==
					WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS and
					not requesting_healer.user.has_perm(Healer.SCHEDULE_PERMISSION)):
				return ('Booking at %s has been disabled because your account has not been paid.' %
					wcenter)
		return False

	def get_form():
		"""Return ScheduleSettingsForm or None if wellness center."""
		if not is_wellnesscenter:
			return ScheduleSettingsForm.create(request, healer)

	def get_tt_and_tl_forms():
		"""Return tuple - treatment type form and treatment length forms."""
		if len(treatment_lengths) == 0:
			return (TreatmentTypeForm(), TreatmentTypeLengthForm())
		else:
			return (None, None)

	def get_names():
		names = {request.user.username: 'All'}
		for provider in providers:
			names[provider.user.username] = str(provider.user.client)
		return json.dumps(names)

	def add_colors_and_names_to_providers(providers):
		output = []
		i = 0
		for provider in providers:
			output.append({
				'healer': provider,
				'username': provider.user.username,
				'name': str(provider.user.client),
				'first_name': provider.user.first_name,
				'color': Location.get_next_color(i, False),
				'profile_url': provider.healer_profile_url(),
				})
			i += 1
		return output

	def get_location_available_treatments():
		""" Return treatment type lengths available for locations (json).
			Example output:
			{1: 43, 2: 45} (location ids - 1,2. 43, 45 - available treatment type lengths)
		"""
		location_available_treatments = {}

		locations = requesting_healer.get_locations_objects()
		if not is_wellnesscenter:
			available_tls = list(TreatmentTypeLength.objects.filter(treatment_type__healer=requesting_healer).values_list('pk', flat=True))
			for location in locations:
				location_available_treatments[location.pk] = available_tls
			locations = requesting_healer.get_center_locations_objects()

		for location in locations:
			location_available_treatments[location.pk] = []
			location_rooms = location.rooms.all()
			for tl in treatment_lengths:
				if (not tl.treatment_type.rooms.exists() or
						location_rooms.filter(
							pk__in=tl.treatment_type.rooms.values_list(
								'pk', flat=True)).exists()):
					location_available_treatments[location.pk].append(tl.pk)

		return json.dumps(location_available_treatments)

	def get_discount_codes():
		def get_healer_codes():
			def get_codes(healer):
				return [{'id': code.pk, 'name': str(code)} for code in DiscountCode.objects.filter(healer=healer)]

			healer_codes = {}
			healer_codes[requesting_healer] = get_codes(requesting_healer)
			for healer in requesting_healer.get_wellness_centers():
				healer_codes[healer] = get_codes(healer)
			return healer_codes

		codes = {}
		healer_codes = get_healer_codes()

		for location in requesting_healer.get_locations_objects():
			codes[location.pk] = healer_codes[requesting_healer]

		for healer in requesting_healer.get_wellness_centers():
			for location in healer.get_locations_objects():
				codes[location.pk] = healer_codes[healer]
		return json.dumps(codes)

	def get_providers_not_paid():
		if (is_wellnesscenter and wcenter.payment_schedule_setting ==
				WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS):
			return [provider
				for provider in get_healers_in_wcenter_with_schedule_editing_perm(wcenter)
				if provider not in providers]

		else:
			return []

	requesting_healer = get_object_or_404(Healer, user=request.user)
	is_wellnesscenter = wcenter = is_wellness_center(requesting_healer)
	username = get_username(request, username)
	healer = get_healer(request.user, username)
	wcenter_healer_has_treatment_types = wcenter_healer_has_treatment_types_(request.user, healer)
	locations = requesting_healer.get_locations()
	treatment_lengths = requesting_healer.get_all_treatment_type_lengths()
	treatment_form, treatment_length_form = get_tt_and_tl_forms()
	all_rooms = get_all_rooms(locations, healer, is_wellnesscenter)
	treatments_locations, treatments_rooms = get_treatments_locations_and_rooms(requesting_healer)
	if request.user.username == 'healcenterojai':
		providers = get_providers(requesting_healer, True)
	else:
		providers = get_providers(requesting_healer)

	#	client_list = set([f['friend'].client for f in friends if f['friend'].client.approval_rating != 0])
	return render_to_response(template_name, dict({
		'healer': healer,
		'confirmedListEndDate': (healer.get_local_day() + timedelta(days=7)).isoformat(),
		'new_user_form': NewUserForm(),  # new client
		'user_has_locations': user_has_locations(),
		'locations': locations,
		'locations_json': json.dumps(locations),
		'treatment_lengths': treatment_lengths,
		'treatment_form': treatment_form,
		'treatment_length_form': treatment_length_form,
		'treatments_locations_json': json.dumps(treatments_locations),
		'treatments_rooms_json': json.dumps(treatments_rooms),
		'setup_times_json': get_setup_times_json(providers),
		'all_rooms': all_rooms,
		'all_rooms_json': json.dumps(all_rooms),
		'confirm_message': request.session.pop('confirm_message', ''),
		'repeat_choices': Appointment.REPEAT_CHOICES,
		'unconfirmed_appt_list': get_unconfirmed_appt_list(),
		'color': (locations[0]['color'] if locations else LOCATION_COLOR_LIST[0]),
		'edit_availaibility': edit_availaibility,
		'form': get_form(),
		'facebook_auth_url': get_facebook_auth_url(request, 'schedule'),
		'clients': autocomplete_hs.views.autocomplete_all_clients(requesting_healer),
		# 'title': get_title(),
		'wcenter_healer_has_treatment_types': wcenter_healer_has_treatment_types,
		'treatment_lengths_locations': get_treatment_lengths_locations(
			healer, locations, treatment_lengths),
		'has_treatments': has_treatments(treatment_lengths, is_wellnesscenter,
			healer, requesting_healer),
		'username': username,
		'names': get_names(),
		'providers': add_colors_and_names_to_providers(providers),
		'providers_not_paid': add_colors_and_names_to_providers(get_providers_not_paid()),
		'is_healers_schedule_not_paid': is_healers_schedule_not_paid(),
		'seen_appointments_help': requesting_healer.seen_appointments_help,
		'provider_treatments': (get_provider_treatments() if is_wellnesscenter else None),
		'location_id': location_id,
		'location_available_treatments': get_location_available_treatments(),
		'discount_codes_json': get_discount_codes(),
		'schedule_trial_number_of_days': settings.SCHEDULE_TRIAL_NUMBER_OF_DAYS,
		'STRIPE_CONNECT_LINK': settings.STRIPE_CONNECT_LINK,
		'payment': settings.PAYMENTS_SCHEDULE_PAYMENT,
	}, **extra_context), context_instance=RequestContext(request))

#@user_authenticated
#def appointments(request, template_name='healers/appointments.html'):
#	healer = get_object_or_404(Healer, user__id=request.user.id)
#
#	if healer.healer_treatment_types.count() == 0:
#		return redirect('treatment_types')
#
#	clients = Clients.objects.friends_for_user(request.user.id)
#	referrals = Referrals.objects.friends_for_user(request.user.id)
#	friends = clients + referrals
#
#	client_list = [f['friend'].client for f in friends if f['friend'].client.approval_rating != 0]
#
#	new_user_form = NewUserForm()
#
##	locations = HealerLocation.objects.select_related('location').filter(healer=healer)
#	locations = healer.get_locations()
#
#	confirm_message = request.session.pop('confirm_message', '')
#
#	appts = Appointment.objects.get_active_json(healer)
#	unconfirmed_appt_list = Appointment.objects.get_active(request.user.client.healer).filter(confirmed=False)
#
#	return render_to_response(template_name, {
#		'other_user': request.user,
#		'defaultTimeslotLengthVar': healer.defaultTimeslotLength,
#		'confirmedListEndDate': (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=7)).isoformat(),
#		'bookAheadDays': healer.bookAheadDays,
#		'client_list': client_list,
#		'new_user_form': new_user_form,
#		'locations': locations,
#		'treatment_types': healer.healer_treatment_types.all().order_by('is_deleted', 'length'),
#		'confirm_message': confirm_message,
#		'repeat_choices': Appointment.REPEAT_CHOICES,
#		'appointment_list': appts,
#		'unconfirmed_appt_list': unconfirmed_appt_list
#	}, context_instance=RequestContext(request))


def get_appointment(user, appointment_id):
	def check_if_appointment_is_editable_by_wcenter():
		wcenter.get_location_ids
		wcenter_locations_ids = wcenter.get_location_ids()
		return appointment.location.pk in wcenter_locations_ids

	appointment = get_object_or_404(Appointment, id=appointment_id)

	# Check access
	wcenter = is_wellness_center(user)
	if wcenter:
		if not check_if_appointment_is_editable_by_wcenter():
			raise Http404
	else:
		if appointment.healer.user != user:
			raise Http404
	return appointment


@user_authenticated
def appointment_confirm(request, appt_id, accept=False):
	appt = get_appointment(request.user, appt_id)

	confirm_message = ''
	if Timeslot.check_for_conflicts(appt.healer, appt.start, appt.end, False, appt, ['appointment']):
		appt.cancel(request.user)
		appt.notify_canceled(appt.healer.user, is_wellness_center(request.user))
		confirm_message = 'This appointment was canceled, because it conflicts with another appointment.'
	#messages.add_message(request, messages.ERROR, 'This conflicts with another appointment.')

	if Vacation.check_for_conflicts(appt):
		confirm_message = ('You have scheduled this appointment during your time off. '
						   'Remember to take care of yourself too!')

	if not appt.canceled:
		appt.confirm()

	if not confirm_message:
		confirm_message = '<strong>Appointment Confirmed:</strong> %s at %s<br><em>%s has been notified by email</em>' %\
						  (appt.date_range_text(), (appt.location.title if appt.location else ''), appt.client)

	request.session['confirm_message'] = confirm_message

	if accept:
		location_user = ClientLocation.objects.get(location=appt.location).client.user
		if wcenter_get_provider(location_user, appt.healer.user.username):
			wcenter_user = location_user
		else:
			wcenter_user = None
		friend_process(request, 'clients', appt.client.user.id, action='accept', wcenter_user=wcenter_user)

	return redirect('appointments', appt.healer.user.username)


@user_authenticated
def appointment_wcenter_confirm_decline_all(request, type):
	wcenter_healer = get_object_or_404(Healer, user=request.user)
	providers = get_healers_in_wcenter_with_schedule_editing_perm(wcenter_healer)
	message = ''
	if type == 'confirm':
		function = confirm_all_appointments
	elif type == 'decline':
		function = decline_all_appointments
	for provider in providers:
		confirm_message = function(request.user, provider.user.username)
		if confirm_message != '':
			message += '<div class="provider-confirm-message">' + provider.user.get_full_name() + '<br>' + confirm_message + '</div>'
	request.session['confirm_message'] = message
	return redirect('appointments')


def confirm_all_appointments(user, username):
	healer = get_healer(user, username)

	appts = Appointment.objects.filter(healer=healer, start_date__gte=healer.get_local_time().date(),
		confirmed=False).order_by('id')

	counter = {'confirmed': 0, 'canceled': 0, 'vacation': 0}
	for appt in appts:
		if Timeslot.check_for_conflicts(healer, appt.start, appt.end, False, appt, ['appointment']):
			appt.cancel(user)
			appt.notify_canceled(healer.user, is_wellness_center(user))
			counter['canceled'] += 1
			continue

		if Vacation.check_for_conflicts(appt):
			counter['vacation'] += 1

		if not appt.canceled:
			appt.confirm()
			counter['confirmed'] += 1

	message = ''
	if counter['canceled']:
		message += (
		'Not all appointments could be confirmed because they conflict with other appointments. '
		'Please check your schedule carefully. ')

	elif counter['confirmed']:
		message += 'Appointments confirmed. '

	if counter['vacation']:
		message += ('You have scheduled some appointments during your time off. '
											   'Remember to take care of yourself too! ')

	return message


@user_authenticated
def appointment_confirm_all(request, username):
	request.session['confirm_message'] = confirm_all_appointments(
		request.user, username)
	return redirect('appointments', username)


@user_authenticated
def appointment_decline(request, appt_id):
	appt = get_appointment(request.user, appt_id)
	appt.cancel(request.user)

	if appt.confirmed:
		appt.notify_canceled(appt.healer.user, is_wellness_center(request.user))
		request.session['confirm_message'] = 'Appointment canceled.'
	else:
		appt.notify_declined(appt.healer.user)
		request.session['confirm_message'] = 'Appointment declined.'

	return redirect('appointments', appt.healer.user.username)


def decline_all_appointments(user, username):
	healer = get_healer(user, username)

	appts = Appointment.objects.filter(healer=healer, start_date__gte=healer.get_local_time().date(),
		confirmed=False).order_by('id')

	if appts.exists():
		for appt in appts:
			appt.cancel(user)
			appt.notify_declined(healer.user)
		return 'Appointments declined.'
	else:
		return ''


@user_authenticated
def appointment_decline_all(request, username):
	request.session['confirm_message'] = decline_all_appointments(
		request.user, username)
	return redirect('appointments', username)

#@user_authenticated
#def availability(request, template_name='healers/availability.html'):
#	healer = get_object_or_404(Healer, user__id=request.user.id)
#
#	if healer.healer_treatment_types.count() == 0:
#		return redirect('treatment_types')
#
##	locations = HealerLocation.objects.filter(healer=healer)
#	locations = healer.get_locations()
#
##	if locations:
##		current_location_id = locations[0]['id']
##	else:
##		current_location_id = -1
##
##	if request.method == 'POST':
##		try:
##			current_location_id = int(request.POST.get('location').encode())
##		except TypeError:
##			pass
#
##	appts = Appointment.objects.get_active_json(healer)
#
#	return render_to_response(template_name, {
#		'defaultTimeslotLengthVar': healer.defaultTimeslotLength,
#		'other_user': request.user,
#		'locations': locations,
##		'current_location_id': current_location_id,
#		'bookAheadDays': healer.bookAheadDays,
#	   'color': (locations[0]['color'] if locations else LOCATION_COLOR_LIST[0]),
#	   'timeslot_list': getTimeslotsEdit(request=request),
#		}, context_instance=RequestContext(request))


@user_authenticated
def vacation(request, template_name='healers/settings/vacation.html', username=None):
	username = get_username(request, username)
	healer = get_healer(request.user, username)
	vacations = Vacation.objects.filter(healer=healer,
		end_date__gte=healer.get_local_time().date()).order_by('start_date')

	if request.method == 'POST':
		form = VacationForm(request.POST)
		if form.is_valid():
			v = Vacation(healer=healer)
			v.set_dates(form.cleaned_data['start'], form.cleaned_data['end'])
			v.end_date = form.cleaned_data['end'].date()
			v.save()

	else:
		default_datetime = datetime.combine(healer.get_local_time().date(), time(12, 0))
		form = VacationForm(initial={
			'start': default_datetime,
			'end': default_datetime,
			})

	return render_to_response(template_name, {
		'vacation_list': vacations,
		'form': form,
		'username': username,
		'healer': healer,
		'is_schedule_settings': True,
		}, context_instance=RequestContext(request))


@user_authenticated
def account(request, error=None):
	def is_schedule_and_notes_options_visible():
		if is_wellness_center(healer):
			return True, True
		wcenters = healer.get_wellness_centers()
		is_schedule_option_visible = False
		is_notes_option_visible = True

		for wc in wcenters:
			if wc.payment_schedule_setting == WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS:
				is_schedule_option_visible = True
			elif wc.payment_schedule_setting == WellnessCenter.PAYMENT_CENTER_PAYS:
				is_notes_option_visible = False
			if is_schedule_option_visible and is_notes_option_visible:
				break
		return is_schedule_option_visible, is_notes_option_visible

	healer = get_object_or_404(Healer, user=request.user)

	is_schedule_option_visible, is_notes_option_visible = is_schedule_and_notes_options_visible()
	return render_to_response('healers/settings/account.html', {
		'username': request.user.username,
		'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
		'error': error,
		'payment_schedule': settings.PAYMENTS_SCHEDULE_PAYMENT,
		'payment_notes': settings.PAYMENTS_NOTES_PAYMENT,
		'payment_schedule_unlim': settings.PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT,
		'is_schedule_option_visible': is_schedule_option_visible,
		'is_notes_option_visible': is_notes_option_visible,
	}, context_instance=RequestContext(request))


@login_required
def remote_session_toggle(request, state):
	healer = get_object_or_404(Healer, user=request.user)
	healer.remote_sessions = state
	healer.save()
	return redirect('location')


@login_required
def location(request, template_name='healers/settings/location.html',
		redirect_url=None, account_setup=False, extra_context={}):
	def save_location():
		location = location_form.save()
		healer_location = ClientLocation(client=healer, location=location)
		healer_location.save()

		# if this is the first location that the user added, set all timeslots and appts to the new location
		# also mark it as default
		if len(locations) == 0:
			# added if clauses because tests fail if update command applied in one line
			timeslots = HealerTimeslot.objects.filter(healer=healer)
			if timeslots:
				timeslots.update(location=location)
			appointments = Appointment.all_objects.filter(healer=healer)
			if appointments:
				appointments.update(location=location)
			location.is_default = True
			location.save()
		return location

	healer = get_object_or_404(Healer, user__id=request.user.id)

	remote_sessions_form = RemoteSessionsForm(request.POST or
		{'remote_sessions': healer.remote_sessions})

	healer_locations = ClientLocation.objects.filter(
		client__user__id=request.user.id, location__is_deleted=False)

	locations = [hl.location for hl in healer_locations]

	location_form = LocationForm(request.POST or None, healer=healer,
		account_setup=account_setup)
	if is_wellness_center(healer):
		room_form = RoomForm()
	else:
		room_form = None
	if request.method == 'POST':
		if account_setup and remote_sessions_form.is_valid():
			healer.remote_sessions = remote_sessions_form.cleaned_data['remote_sessions']
			healer.save()

		if location_form.is_valid() or healer.remote_sessions:
			if location_form.is_valid():
				location = save_location()
				if is_wellness_center(healer):
					Room(location=location, name='Default Room').save()

			if redirect_url:
				return redirect(redirect_url)
			else:
				return redirect('location')

		if not location_form.is_valid():
			if account_setup:
				if location_form.errors['title'][0] == 'This field is required.':
					location_form.errors['__all__'] = ['You must either set your location OR choose "Yes" for remote sessions']
					location_form.errors.pop('title')

	return render_to_response(template_name, dict({
		'location_list': locations,
		'location_form': location_form,
		'room_form': room_form,
		'remote_sessions_form': remote_sessions_form,
		'username': healer.user.username,
	}, **extra_context), context_instance=RequestContext(request))


@user_authenticated
def location_edit(request, location_id):
	def get_template():
		if is_wellness_center(healer):
			return 'healers/settings/location_edit_single_page.html'
		return 'healers/settings/location_edit.html'

	healer = get_object_or_404(Healer, user__id=request.user.id)
	healer_location = get_object_or_404(ClientLocation, client__user__id=request.user.id, location__id=location_id)

	form = LocationForm(request.POST or None, instance=healer_location.location, healer=healer_location.client.healer)
	if form.is_valid():
		form.save()
	#		return redirect('location_edit', healer_location.location.id)

	return render_to_response(get_template(), {
		'form': form,
		'location': healer_location.location,
		'username': healer.user.username,
		'is_schedule_settings': True,
		}, context_instance=RequestContext(request))


@user_authenticated
def location_delete(request, location_id):
	client_location = get_object_or_404(
		ClientLocation,
		location__id=location_id,
		client__user=request.user)
	location = client_location.location

	locations_count = ClientLocation.objects.filter(
		client__user=request.user,
		location__is_deleted=False).count()
	if locations_count > 1:
		location.delete()
		HealerTimeslot.objects.filter(location=location).delete()

	return redirect('location')


@user_authenticated
def location_default(request, location_id):
	healer_location = get_object_or_404(
		ClientLocation, client__user__id=request.user.id, location__id=location_id)

	client_locations = ClientLocation.objects.filter(
		client__user__id=request.user.id,
		location__is_deleted=False,
		location__is_default=True)
	for cl in client_locations:
		cl.location.is_default = False
		cl.location.save()

	healer_location.location.is_default = True
	healer_location.location.save()

	return redirect('location')


@user_authenticated
def copy_my_treatment_types(request, wcenter_id):
	def email_wcenter():
		from_email = settings.DEFAULT_FROM_EMAIL
		to_email = wcenter.user.email
		subject_template = 'healers/emails/copy_my_treatment_types_subject.txt'
		message_template = 'healers/emails/copy_my_treatment_types_message.txt'
		subject = render_to_string(subject_template, {'healer': healer})
		send_hs_mail(subject, message_template, {
			'treatment_types': treatment_types_new}, from_email, [to_email])

	def check_added_treatment_types():
		treatment_types = WellnessCenterTreatmentType.objects.get_or_create(
			wellness_center=wcenter,
			healer=healer)[0].treatment_types

		[treatment_types.add(tt) for tt in treatment_types_new]
		[treatment_types.add(tt) for tt in treatment_types_to_check_existing]

	wcenter = get_object_or_404(WellnessCenter, pk=wcenter_id)
	healer = wcenter_get_provider(wcenter, request.user.username)
	if healer is not None:
		wcenter_treatment_types = wcenter.healer_treatment_types.exclude(is_deleted=True)
		treatment_types = healer.healer_treatment_types.exclude(is_deleted=True)
		treatment_types_new = []
		treatment_types_to_check_existing = []
		for treatment_type in treatment_types:
			wcenter_tt = wcenter_treatment_types.filter(title__iexact=treatment_type.title)
			if not wcenter_tt.exists():
				# duplicate treatment type
				tt = deepcopy(treatment_type)
				tt.pk = None
				tt.healer = wcenter.healer
				tt.save()

				# duplicate lengths
				lengths = treatment_type.lengths.exclude(is_deleted=True)
				for length in lengths:
					l = length
					l.pk = None
					l.treatment_type = tt
					l.save()
				treatment_types_new.append(tt)
			else:
				treatment_types_to_check_existing.append(wcenter_tt[0])

		if treatment_types_new:
			email_wcenter()

		check_added_treatment_types()

	return redirect('treatment_types')


def get_available_locations(user):
	if is_wellness_center(user):
		return get_wcenter_location_ids(user)


def get_wcenter_tts(healer_center):
	# Included this code because test isn't working otherwise. Works fine on website however.
	try:
		WellnessCenterTreatmentType.objects.get(**healer_center)
	except:
		WellnessCenterTreatmentType(**healer_center).save()
	return WellnessCenterTreatmentType.objects.get_or_create(
		**healer_center)[0].treatment_types


@login_required
def treatment_types(request, template_name='healers/settings/treatment_types.html', extra_context={}, username=None):
	def get_wellness_centers_treatment_types():
		''' Returns tuple (wellness_centers_treatment_types, is_selected_wcenter_treatment_type)
		wellness_centers_treatment_types - a dict {wcenter_id: {'name': wcenter name, 'types': treatment types}}
		is_selected_wcenter_treatment_type - bool - True if selected at least one treament type in one of wcenters
		'''
		def get_wellness_centers():
			wellness_center = is_wellness_center(request.user)
			if wellness_center:
				if wellness_center.healer == healer:
					return []
				else:
					return [wellness_center]
			else:
				return healer.get_wellness_centers()

		def get_selected_treatment_types():
			wellness_centers_treatment_types = []
			for wellness_center in wellness_centers:
				wellness_centers_treatment_types += WellnessCenterTreatmentType \
					.objects.get_or_create(healer=healer, wellness_center=wellness_center)[0] \
					.treatment_types.all().values_list('pk', flat=True)
			return wellness_centers_treatment_types

		def get_treatment_lengths(treatment_type_id):
			def get_selected_treatment_type_lengths():
				wellness_centers_treatment_type_lengths = []
				for wellness_center in wellness_centers:
					wellness_centers_treatment_type_lengths += WellnessCenterTreatmentTypeLength \
						.objects.get_or_create(healer=healer, wellness_center=wellness_center)[0] \
						.treatment_type_lengths.filter(treatment_type__pk=treatment_type_id).values_list('pk', flat=True)
				return wellness_centers_treatment_type_lengths

			lengths_output = []
			selected_treatment_type_lengths = get_selected_treatment_type_lengths()
			lengths = TreatmentTypeLength.objects.filter(treatment_type__pk=treatment_type_id, is_deleted=False)

			for length in lengths:
				lengths_output.append({
					'id': length.pk,
					'title': str(length),
					'selected': length.pk in selected_treatment_type_lengths
				})
			return lengths_output

		wellness_centers = get_wellness_centers()
		wellness_centers_treatment_types = {}
		selected_treatment_types = get_selected_treatment_types()
		for wellness_center in wellness_centers:
			treatment_types = TreatmentType.objects.filter(healer=wellness_center,
				is_deleted=False).values('id', 'title')
			for treatment_type in treatment_types:
				treatment_type['selected'] = treatment_type['id'] in selected_treatment_types
				treatment_type['lengths'] = get_treatment_lengths(treatment_type['id'])
			wellness_centers_treatment_types[wellness_center.id] = {
				'name': wellness_center.user.get_full_name(),
				'types': treatment_types}
		is_selected_wcenter_treatment_type = selected_treatment_types != []
		return wellness_centers_treatment_types, is_selected_wcenter_treatment_type

	username = get_username(request, username)
	healer = get_healer(request.user, username)

	available_locations = get_available_locations(request.user)

	form = TreatmentTypeForm(available_locations, request.POST or None)
	length_form = TreatmentTypeLengthForm(request.POST or None)
	if form.is_valid() and length_form.is_valid():
		redirect_to = request.POST.get('redirect', False)

		treatment_type = form.save(commit=False)
		treatment_type.healer = healer
		if TreatmentType.objects.filter(healer=healer, is_deleted=False, is_default=True).count() < 1:
			treatment_type.is_default = True
		treatment_type.save()

		# add center treatment type to healer
		if 'healer_id' in request.POST:
			provider = Healer.objects.get(pk=request.POST['healer_id'])
			provider_username = provider.user.username
			wcenter = is_wellness_center(request.user)
			# check if healer is in center. Raise 404 if not.
			get_healer(wcenter.user, provider_username)

			healer_center = {
				'healer': provider,
				'wellness_center': wcenter
			}
			wellness_center_tts = get_wcenter_tts(healer_center)
			wellness_center_tts.add(treatment_type.pk)

			redirect_to = reverse('treatment_types', args=[provider_username])

		for room_id in request.POST.getlist('rooms', []):
			room = Room.objects.get(pk=room_id)
			if room.location.id in available_locations:
				treatment_type.rooms.add(room)

		treatment_length = length_form.save(commit=False)
		treatment_length.treatment_type = treatment_type
		treatment_length.save()

		#blank out the 'add' form
		form = TreatmentTypeForm(available_locations, None)
		length_form = TreatmentTypeLengthForm()

		if redirect_to:
			return redirect(redirect_to)

	wellness_centers_treatment_types, is_selected_wcenter_treatment_type = get_wellness_centers_treatment_types()
	return render_to_response(template_name, dict({
		'treatment_types': TreatmentType.objects.filter(healer=healer, is_deleted=False).order_by('title'),
		'treatment_form': form,
		'treatment_length_form': length_form,
		'wellness_center_treatment_types': wellness_centers_treatment_types,
		'is_selected_wcenter_treatment_type': is_selected_wcenter_treatment_type,
		'username': healer.user.username,
		'healer': healer,
		'healer_name': healer.user.get_full_name(),
		'is_schedule_settings': True,
		}, **extra_context), context_instance=RequestContext(request, ))


@login_required
def treatment_type_edit(request, treatment_type_id):
	treatment_type = get_object_or_404(TreatmentType, id=treatment_type_id, healer__user=request.user)
	available_locations = get_available_locations(request.user)
	form = TreatmentTypeForm(available_locations, request.POST or None, instance=treatment_type)
	length_form = TreatmentTypeLengthForm(request.POST or None)
	if form.is_valid():
		form.save()

		# save rooms - in order to check if room is available at that location
		treatment_type.rooms.clear()
		for room_id in request.POST.getlist('rooms', []):
			room = Room.objects.get(pk=room_id)
			if room.location.id in available_locations:
				treatment_type.rooms.add(room)

		if 'add_length' in request.POST:
			if length_form.is_valid():
				treatment_length = length_form.save(commit=False)
				treatment_length.treatment_type = treatment_type
				treatment_length.save()
				return redirect('treatment_type_edit', treatment_type.id)
		else:
			return redirect('treatment_types')

	return render_to_response('healers/settings/treatment_type_edit.html', {
		'treatment_lengths': treatment_type.lengths.filter(is_deleted=False),
		'treatment_form': form,
		'treatment_length_form': length_form,
		'treatment': treatment_type,
		'username': request.user.username,
		'is_schedule_settings': True,
		}, context_instance=RequestContext(request))


@login_required
def treatment_type_delete(request, treatment_type_id):
	treatment_type = get_object_or_404(TreatmentType, id=treatment_type_id, healer__user=request.user)

	treatment_types = TreatmentType.objects\
		.filter(healer__user=request.user)\
		.filter(is_deleted=False)
	if treatment_types.count() > 1:
		treatment_type.delete()

	return redirect('treatment_types')


@user_authenticated
def treatment_type_default(request, treatment_type_id):
	treatment_type = get_object_or_404(TreatmentType, id=treatment_type_id, healer__user=request.user)

	treatment_type.set_default()

	return redirect('treatment_types')


@user_authenticated
def save_wcenter_treatment_types(request, username):
	def save_treatment_types():
		wellness_center_tts = get_wcenter_tts(healer_center)
		wellness_center_tts.clear()
		for type_id in json.loads(request.POST.get('types', '[]')):
			wellness_center_tts.add(type_id)

	def save_treatment_type_lengths():
		wellness_center_ttls = WellnessCenterTreatmentTypeLength.objects.get_or_create(
			**healer_center)[0].treatment_type_lengths
		wellness_center_ttls.clear()
		for id in json.loads(request.POST.get('type_lengths', '[]')):
			wellness_center_ttls.add(id)

	healer = get_healer(request.user, username)

	healer_center = {
		'healer': healer,
		'wellness_center': WellnessCenter.objects.get(pk=request.POST['wcenter_id'])
	}

	save_treatment_types()
	save_treatment_type_lengths()

	return redirect(reverse('treatment_types', args=[username]))


@user_authenticated
def treatment_length_add(request, treatment_type_id):
	treatment_type = get_object_or_404(TreatmentType, id=treatment_type_id, healer__user=request.user)

	length_form = TreatmentTypeLengthForm(request.POST or None)
	if length_form.is_valid():
		treatment_length = length_form.save(commit=False)
		treatment_length.treatment_type = treatment_type
		treatment_length.save()

		if request.POST.get('redirect'):
			return redirect(request.POST.get('redirect'))
		else:
			return redirect('treatment_types')
	return redirect('treatment_types')


@user_authenticated
def treatment_length_delete(request, treatment_length_id):
	treatment_length = get_object_or_404(TreatmentTypeLength,
		id=treatment_length_id,
		treatment_type__healer__user=request.user)

	if treatment_length.treatment_type.lengths.filter(is_deleted=False).count() > 1:
		treatment_length.delete()

	return redirect('treatment_type_edit', treatment_length.treatment_type_id)


@user_authenticated
def treatment_length_default(request, treatment_length_id):
	treatment_length = get_object_or_404(TreatmentTypeLength,
		id=treatment_length_id,
		treatment_type__healer__user=request.user)

	treatment_length.set_default()

	return redirect('treatment_type_edit', treatment_length.treatment_type_id)


def check_if_location_belongs_to_user(location, user):
	get_object_or_404(ClientLocation, location=location, client__user=user)


@user_authenticated
def room_add(request, location_id):
	location = get_object_or_404(Location, id=location_id, is_deleted=False)
	check_if_location_belongs_to_user(location, request.user)
	room_form = RoomForm(request.POST or None)
	if room_form.is_valid():
		room_form = room_form.save(commit=False)
		room_form.location = location
		room_form.save()
	return redirect('location')


@user_authenticated
def room_delete(request, room_id):
	room = get_object_or_404(Room, id=room_id)
	location = room.location
	check_if_location_belongs_to_user(location, request.user)

	if location.rooms.count() > 1:
		room.delete()

	return redirect('location')


@user_authenticated
def room_edit(request, room_id):
	room = get_object_or_404(Room, id=room_id)
	check_if_location_belongs_to_user(room.location, request.user)
	room_form = RoomForm(request.POST or None, instance=room)
	if room_form.is_valid():
		room_form.save()
		return redirect('location')
	return render_to_response('healers/room_edit.html',
		{
			'room_form': room_form,
			'room_id': room_id,
		},
		context_instance=RequestContext(request))


@user_authenticated
def vacation_delete(request, vacation_id):
	vacation = get_object_or_404(Vacation, id=vacation_id)
	username = vacation.healer.user.username
	get_healer(request.user, vacation.healer.user.username)  # check permission to delete vacation
	vacation.delete()
	return redirect('vacation', username) if username else redirect('vacation')


@user_authenticated
def clients(request, provider_username):
	provider = get_object_or_404(Healer, user__username__iexact=provider_username)
	clients = [o['friend'] for o in Clients.objects.friends_for_user(request.user)]
	referrals_from_me = [o['friend'] for o in Referrals.objects.referrals_from(request.user)]
	for r in referrals_from_me:
		r.recommended = True
		clients.append(r)

	phones = ContactPhone.objects.values_list('contact__client__user__id', 'number').\
		filter(contact__healer__user=request.user, contact__client__user__in=clients)
	phones = dict([(phone[0], phone[1]) for phone in phones])
	for user in clients:
		user.contact_phone = phones.get(user.id, '')

	emails = ContactEmail.objects.values_list('contact__client__user__id', 'email').\
		filter(contact__healer__user=request.user, contact__client__user__in=clients)
	emails = dict([(email[0], email[1]) for email in emails])
	for user in clients:
		user.contact_email = emails.get(user.id, '')

	clients = sorted(clients, key=lambda u: u.first_name.lower())

	return render_to_response('healers/clients_list.html',
		{
			'friend_type': 'clients',
			'friends': clients,
			'refer_provider': provider
		},
		context_instance=RequestContext(request))


@user_authenticated
def providers(request, client_username):
	client = get_object_or_404(Client, user__username__iexact=client_username)

	providers = [o['friend'] for o in Referrals.objects.referrals_from(request.user)]

	providers = sorted(providers, key=lambda u: u.first_name.lower())

	return render_to_response('healers/providers_list.html',
		{
			'friend_type': 'referrals',
			'friends': providers,
			'refer_client': client
		},
		context_instance=RequestContext(request))


@user_authenticated
def refer_client(request, provider_username, client_username, email_to_provider=True):
	provider = get_object_or_404(Healer, user__username__iexact=provider_username)
	client = get_object_or_404(Client, user__username__iexact=client_username)

	is_client = is_my_client(provider.user, client.user)
	is_referral_sent = ReferralsSent.objects.filter(
		provider_user=provider.user,
		client_user=client.user,
		referring_user=request.user).count()

	if not is_client and not is_referral_sent:
		friendship = Clients(from_user=provider.user, to_user=client.user)
		friendship.save()

		ReferralsSent.objects.create(
			provider_user=provider.user,
			client_user=client.user,
			referring_user=request.user)

		if email_to_provider:
			ctx = {
				'SITE_NAME': settings.SITE_NAME,
				'client': client,
				'client_info':	client.contact_info(),
				'referer': request.user
			}
			subject = render_to_string('friends/refer_client_to_provider_subject.txt', ctx)
			send_hs_mail(subject,
				'friends/refer_client_to_provider_message.txt',
				ctx,
				settings.DEFAULT_FROM_EMAIL,
				[provider.user.email])
		else:
			friendship, is_profile_visible, ctx = get_healer_info_context(provider, request)
			ctx['info_only'] = True

			ctx.update({
				'SITE_NAME': settings.SITE_NAME,
				'STATIC_URL': settings.STATIC_URL,
				'provider': provider,
				'referer': request.user
			})
			subject = render_to_string('friends/refer_provider_to_client_subject.txt', ctx)
			send_hs_mail(subject,
				'friends/refer_provider_to_client_message.txt',
				ctx,
				settings.DEFAULT_FROM_EMAIL,
				[client.user.email],
				html_template_name='friends/refer_provider_to_client_message.html'
				)

		#update refers model

		message = 'You refered %s to %s.' % (client, provider.client_ptr)
	else:
		message = '%s was already a client of %s.' % (client, provider.client_ptr)

	return render_to_response('healers/refer_result.html',
		{
			'message': message,
		},
		context_instance=RequestContext(request))


@login_required
def friends(request, friend_type, template_name=None, extra_context=None):
	if extra_context is None:
		extra_context = {}

#	FriendClass, InvitationClass = get_friend_classes(friend_type)

	invitations = []
	referrals_to_me = None
	referrals_from_me = None
	clients_users = [o['friend'] for o in Clients.objects.friends_for_user(request.user)]
	other_friends = clients_users
	suggested_recommendations = []

	recommended_providers = None
	if friend_type == 'healers':
		template_name = 'clients/my_providers.html'
		from friends_app.recommendations import ClientRecommendationsFinder
		recommended_providers = Healer.objects.filter(user__in=ClientRecommendationsFinder(request).recommendations)

	else:
		healer = get_object_or_404(Healer, user=request.user)
		if friend_type == 'providers' and not is_wellness_center(healer):
			raise Http404

		referrals_from_me = [o['friend'] for o in Referrals.objects.referrals_from(request.user)]

		if friend_type in ['referrals', 'providers']:
			# if is_wellness_center(healer) and healer.setup_step == 6:
			# 	if not hasattr(request, 'step'):
			# 		return redirect(reverse('provider_setup', args=(6,)))
			# else:
			if template_name is None:
				template_name = 'healers/%s.html' % friend_type

			other_friends = referrals_from_me

			referrals_sent = ReferralsSent.objects.select_related('provider_user', 'client_user', 'referring_user').filter(Q(provider_user=request.user) | Q(referring_user=request.user))
			appts_users = (r.client_user for r in referrals_sent)
			appts_count_from = Appointment.objects.estimate_number(appts_users, request.user.client.healer)

			for user in other_friends:
				referrals_to_someone = [r.client_user for r in referrals_sent
										if r.provider_user == user and r.referring_user == request.user]

				user.referrals_to = len(referrals_to_someone)
				user.appointments_to = 0
				if user.referrals_to:
					appts_count_to = Appointment.objects.estimate_number(appts_users, user.client.healer)
					user.appointments_to = sum(
						v for k, v in appts_count_to.iteritems() if k in referrals_to_someone)

			referrals_to_me = [o['friend'] for o in Referrals.objects.referrals_to(request.user)]
			referrals_to_me = sorted(referrals_to_me, key=lambda u: u.first_name.lower())
			for user in referrals_to_me:
				referrals_from_someone = [r.client_user for r in referrals_sent
											if r.provider_user == request.user and r.referring_user == user]

				user.referrals_from = len(referrals_from_someone)
				user.appointments_from = 0
				if user.referrals_from:
					user.appointments_from = sum(v for k,v in appts_count_from.iteritems() if k in referrals_from_someone)
				if user in other_friends:
					user.me_refered = True

			from friends_app.recommendations import ProviderRecommendationsFinder
			suggested_recommendations = ProviderRecommendationsFinder(request, referrals_from_me, recommendations_limit=4).recommendations

		else:  # if friend_type == 'clients':
			template_name = 'healers/clients.html'

			for r in referrals_from_me:
				r.recommended = True
				other_friends.append(r)

			phones = ContactPhone.objects.values_list('contact__client__user__id', 'number').filter(contact__healer__user=request.user, contact__client__user__in=other_friends)
			phones = dict([(phone[0], phone[1]) for phone in phones])
			for user in other_friends:
				user.contact_phone = phones.get(user.id, '')

			emails = ContactEmail.objects.values_list('contact__client__user__id', 'email').filter(contact__healer__user=request.user, contact__client__user__in=other_friends)
			emails = dict([(email[0], email[1]) for email in emails])
			for user in other_friends:
				user.contact_email = emails.get(user.id, '')

	other_friends = sorted(other_friends, key=lambda u: u.first_name.lower())

	contacts_list = None
	join_request_form = None
	has_treatments = None

	if friend_type == 'clients' or friend_type == 'referrals':
		invitations, contacts_list = get_imported_contacts(request.user, clients_users, referrals_from_me)

		try:
			client = request.user.client
			form_initial = {'message': client.invite_message}
		except Exception:
			client = None
			form_initial = {}
		form_initial['invite_type'] = 'client' if friend_type == 'clients' else 'provider'
		join_request_form = ContactsJoinInviteRequestForm(initial=form_initial, user=request.user)

	#	search_form = ClientsSearchForm(search_type=friend_type)

	msg = request.session.get('message', None)

	if msg is not None:
		request.session['message'] = None

	if friend_type == 'providers':
		healers = Healer.objects.filter(user__in=other_friends)
		other_friends = {'complete': {'editable': [], 'uneditable': []}, 'incomplete': []}
		has_treatments = healer.healer_treatment_types.exists()
		for h in healers:
			key = 'incomplete' if h.is_fill_warning() or not h.is_confirmed_email() else 'complete'
			if key == 'complete':
				if wcenter_get_provider(request.user, h.user.username):
					key2 = 'editable'
				else:
					key2 = 'uneditable'
				other_friends[key][key2].append(h.user)
			else:
				other_friends[key].append(h.user)

	request.friend_type = friend_type	   # this gets accessed in friend_processor. Dont touch it

	return render_to_response(template_name, dict({
		'incomplete_intake_form_answers': request.user.client.incomplete_forms(),
		'invitations': invitations,
		'friends': other_friends,
		'referrals_to_me': referrals_to_me,
		'suggested_recommendations': suggested_recommendations,
		'contacts': contacts_list,
		'join_request_form': join_request_form,
		'facebook_auth_url': get_facebook_auth_url(request, 'friends', args=['clients']),
		#			 'search_form': search_form,
		'is_to_healer': friend_type == 'referrals',
		'new_user_form': NewUserForm(),
		'message': msg,
		'wellness_center': is_wellness_center(request.user),
		'recommended_providers': recommended_providers,
		'existing_user_error': request.session.pop('existing_user_error', None),
		'existing_provider_request_permission': request.session.pop('existing_provider_request_permission', None),
		'has_treatments': has_treatments,
	}, **extra_context), context_instance=RequestContext(request, {}, [friend_processor]))

#@user_authenticated
#def friends_search(request, friend_type, template_name='healers/friends_search.html', **kwargs):
#	form_class = kwargs.get('form_class', ClientsSearchForm)
#	form = form_class(request.GET or None, search_type=friend_type)
#	found_clients = []
#	message = ''
#	if form.is_valid():
#		found_clients = form.search(my_client_id=request.user.client.id)
#		if not found_clients:
#			message = 'Your search didn't match any results. Please Try Again.'
#	else:
#		message = 'Your search didn't match any results. Please Try Again.'
#
#	return render_to_response(template_name, dict({
#			 'friend_type': friend_type,
#			 'search_form': form,
#			 'found_clients': found_clients,
#			 'message': message
#			 }), context_instance=RequestContext(request, {}))

#@user_authenticated


def get_healers_geosearch(
		request, count=None, point=None, modality_category_id=None,
		modality_id=None, name_or_email=None, no_geosearch=False,
		exclude_providers=None, exclude_users=None, schedule_visibility=None,
		random_order=False, distance=50, exclude_centers=False,
		remote_sessions=False, filter_by_referral=None):

	#	try:
	#		ip = request.META['HTTP_X_FORWARDED_FOR']
	#	except KeyError:
	#		ip = request.META['REMOTE_ADDR']

	if not point and not no_geosearch:
		point = request.session.get('point', None)

	#		if not point:
	#			if ip == '127.0.0.1':
	#				zip = Zipcode.objects.get(code='02134')
	#				point = zip.point
	#			else:
	#				geoip = GeoIP()
	#				point = geoip.geos(ip)
	#				request.session['geoip'] = 'true'
	#
	#			request.session['point'] = point

	#	providers = Healer.objects.all()

	# This wont work due to Django bug
	#	providers = Healer.objects.exclude(Q(about='') | Q(user__avatar__isnull=True) | Q(clientlocation__isnull=True))

	providers = Healer.complete
	#	.filter(clientlocation__isnull=False)\

	if remote_sessions:
		providers = providers.filter(remote_sessions=True)

	if exclude_centers:
		all_centers_ids = WellnessCenter.objects.all().values_list('pk', flat='True')
		providers = providers.exclude(pk__in=all_centers_ids)

	if schedule_visibility is not None:
		providers = providers.filter(scheduleVisibility=schedule_visibility)

	if point:
		providers = providers.filter(
			clientlocation__location__point__distance_lte=(point, D(mi=distance)))
	#		providers = providers.extra(select={'distance': '(ST_distance_sphere(healers_address.point,%s))' % str(PostGISAdapter(point)).replace('%', '%%')})
	#		providers = providers.order_by('distance')
	#	else:
	#		providers = providers.all()

	if exclude_providers:
		providers = providers.exclude(id__in=[h.id for h in exclude_providers])
	if exclude_users:
		providers = providers.exclude(
			user__id__in=[u.id for u in exclude_users])

	#	if request.user.is_authenticated():
	#		providers = providers.exclude(profileVisibility=Healer.VISIBLE_CLIENTS)
	#	else:
	#		providers = providers.exclude(Q(profileVisibility=Healer.VISIBLE_CLIENTS) | Q(profileVisibility=Healer.VISIBLE_REGISTERED))

	if modality_category_id:
		providers = providers.filter(modality__category=modality_category_id)
	elif modality_id:
		providers = providers.filter(modality=modality_id)

	if filter_by_referral:
		referrals = Referrals.objects.referrals_from(filter_by_referral)
		referral_users = [o['friend'].id for o in referrals]
		providers = providers.filter(user__id__in=referral_users)

	if name_or_email:
		providers = ClientsSearchForm.search_by_name_or_email(providers,
															  name_or_email)

	if random_order:
		# additional query because of error: for SELECT DISTINCT, ORDER BY expressions must appear in select list
		providers = Healer.objects.filter(id__in=providers).order_by('?')
		providers = list(providers)
	else:
		#TODO: when moving to django 1.6 or later check https://code.djangoproject.com/ticket/14930
		providers = providers\
			.extra(select={
				'reviews_cnt': 'SELECT COUNT ("review_review"."id") '
							   'FROM "review_review" '
							   'WHERE "review_review"."healer_id"='
							   '"healers_healer"."client_ptr_id"',
				'referrals_cnt': 'SELECT COUNT ("friends_friendship"."id") '
								 'FROM "friends_friendship" '
								 'WHERE "friends_friendship"."to_user_id"='
								 '"auth_user"."id" AND '
								 '"friends_friendship"."from_user_id" IN ('
								 'SELECT "clients_client"."user_id" '
								 'FROM "healers_healer"'
								 'INNER JOIN "clients_client" '
								 'ON ("healers_healer"."client_ptr_id" = '
								 '"clients_client"."id"))'
			})\

		providers = providers\
			.extra(order_by=['scheduleVisibility',
							 '-referrals_cnt', '-reviews_cnt'])


	more = len(providers) > count

	if count:
		return providers[:count], more

	else:
		return providers, False


@user_authenticated
def friend_process(request, friend_type, user_id, action='', refers_to=None, wcenter_user=None):
	client = get_object_or_404(Client, user__id=user_id)
	other_user = client.user

	FriendClass, InvitationClass = get_friend_classes(friend_type)

	if not FriendClass:
		return redirect(client.get_full_url())

	redirect_to = None
	if action == 'invite':
		#only using invites for clients requesting to be a client of a provider
		invite_or_create_client_friendship(client_user=request.user, healer_user=other_user, send_client_request_email=True)

	elif action == 'accept' or action == 'decline':
		if wcenter_user is not None:
			user = wcenter_user
		else:
			user = request.user
		invitations = InvitationClass.objects.filter(from_user=other_user, to_user=user, status=2)
		if invitations:
			invitation = invitations[0]

			#			if friend_type == 'referrals':
			#				are_friends = Referrals.objects.refers_to(invitation.from_user, invitation.to_user)
			#			else:
			#				are_friends = FriendClass.objects.are_friends(invitation.to_user, invitation.from_user)

			status_changed = True
			if action == 'accept':
				# Yes this is correct. Invitation is from client to provider.
				# Client friendship is from provider to client
				if not FriendClass.objects.refers_to(invitation.to_user, invitation.from_user):
					try:
						friendship = Clients(from_user=invitation.to_user, to_user=invitation.from_user)
						friendship.save()
					except IntegrityError:
						connection._rollback()

				status_changed = invitation.status != '5'
				invitation.status = '5'
				invitation.save()

			elif action == 'decline':
				status_changed = invitation.status != '6'
				invitation.status = '6'
				invitation.save()

			invitations.exclude(id=invitation.id).update(status=6)

			if status_changed and is_healer(request.user):
				ctx = {
					'action': 'approve' if action=='accept' else 'decline',
					'healer_name': unicode(request.user.client),
					'login_url': request.build_absolute_uri(reverse('login_page'))
				}

				subject = render_to_string('friends/friend_process_subject.txt', ctx)
				send_hs_mail(subject, 'friends/friend_process_message.txt', ctx, settings.DEFAULT_FROM_EMAIL, [other_user.email])

	elif action == 'remove':
		if (is_healer(request.user)):
			FriendClass.objects.remove(request.user, other_user)
		else:
			FriendClass.objects.remove_bidirectional(request.user, other_user)

	elif action == 'remove_referral':
		Referrals.objects.remove(other_user, refers_to)

		wcenter = is_wellness_center(other_user.client)
		if wcenter:
			provider_to = get_object_or_404(Healer, user__id=refers_to)
			provider_to.wellness_center_permissions.remove(wcenter)

			redirect_to = reverse('friends', args=['providers'])

		else:
			redirect_to = reverse('friends', args=['referrals'])

	elif action == 'approve':
		if not is_my_client(request.user, other_user):
			FriendClass.objects.create(from_user=request.user, to_user=other_user)
		client.approval_rating = 100
		client.save()

	elif action == 'add':
		if friend_type == 'referrals':
			Clients.objects.filter(from_user=request.user, to_user=other_user).delete()

		is_client = is_my_client(request.user, other_user)

		if not is_client and not request.user == other_user:
			friendship = FriendClass(from_user=request.user, to_user=other_user)
			friendship.save()

		if not is_dummy_user(other_user) and is_wellness_center(request.user) and is_healer(other_user):
			ctx = {
				'wellness_center': str(request.user.client),
				'wcenter_permission_url': request.build_absolute_uri(reverse('add_wellness_center_permission', args=[request.user.username]))
			}

			subject = render_to_string('healers/emails/provider_create_subject.txt', ctx)
			send_hs_mail(subject, 'healers/emails/existing_provider_create_message.txt', ctx, request.user.email, [other_user.email])

			redirect_to = reverse('friends', args=['providers'])

		elif friend_type == 'referrals' and not is_wellness_center(request.user):
			profile = request.user.client
			recommend_url = None
			if not FriendClass.objects.filter(from_user=other_user, to_user=request.user).count():
				recommend_url = request.build_absolute_uri(reverse('friend_add', args=['referrals', request.user.id]))
			ctx = {
				'SITE_NAME': settings.SITE_NAME,
				'provider_name': str(profile),
				'provider_profile_url': profile.healer.get_full_url(),
				'recommend_url': recommend_url
			}
			subject = render_to_string('friends/friend_recommend_subject.txt', ctx)
			send_hs_mail(subject, 'friends/friend_recommend_message.txt', ctx, settings.DEFAULT_FROM_EMAIL, [other_user.email])

			redirect_to = reverse('friends', args=['referrals'])

		else:
			redirect_to = reverse('friends', args=['healers'])

	redirect_to = redirect_to if redirect_to else request.META.get('HTTP_REFERER', None)
	if redirect_to and not '/login' in redirect_to:
		return redirect(redirect_to)
	else:
		return redirect('/')


@login_required
def photo_edit(request, extra_context={}, next_override=None, username=None):
	def _get_next(request):
		# next = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', None)))
		next = request.POST.get('next', request.GET.get('next', None))
		if not next or reverse('healer_edit') in next:
			next = request.path
		return next

	username = get_username(request, username)
	if is_healer(request.user):
		user = get_healer(request.user, username).user
	else:
		user = request.user

	avatars = Avatar.objects.filter(user=user).order_by('-primary')
	kwargs = {'avatars': avatars}
	if avatars.count() > 0:
		avatar = avatars[0]
		kwargs['initial'] = {'choice': avatar.id}
	else:
		avatar = None

	client = user.client
	gallery = client.gallery_set.all().order_by('order')
	primary_avatar_form = PrimaryAvatarForm(request.POST or None, user=user, **kwargs)
	form = VideoForm(initial={'videotype': ClientVideo.VIDEO_TYPE_GALLERY})
	error = ''

	def process_form():
		def change_path_if_file_exists(path):
			"""Check if avatar with the same filename already exists for this user and rename the file in this case."""
			def rename_file_if_duplicate(path):
				file_name, extension = path.rsplit('.', 1)
				matches = re.search('(.+?)-(\d+)$', file_name)
				if matches:
					new_file_name = matches.group(1)
					n = int(matches.group(2)) + 1
				else:
					new_file_name = file_name
					n = 2
				return '%s-%d.%s' % (new_file_name, n, extension)

			if Avatar.objects.filter(user=user, avatar=path).exists():
				path = rename_file_if_duplicate(path)
				return change_path_if_file_exists(path)
			else:
				return path

		updated = False
		if 'avatar' in request.FILES:
			file_type = imghdr.what(request.FILES['avatar'])
			uploaded_filename = request.FILES['avatar'].name
			if is_correct_image_file_type(file_type, uploaded_filename):
				path = avatar_file_path(user, file_type, uploaded_filename)
			else:
				return 'Incorrect file type. Only files of type %s are allowed. Please try again.' % ', '.join(settings.ALLOWED_IMAGE_UPLOAD_TYPES)

			path = change_path_if_file_exists(path)
			avatar = Avatar(user=user, avatar=path, primary=True)

			avatar.avatar.storage.save(path, request.FILES['avatar'])
			avatar.save()
			updated = True
			client.gallery_set.latest().change_order(1)

		if 'choice' in request.POST and primary_avatar_form.is_valid():
			avatar = Avatar.objects.get(
				id=primary_avatar_form.cleaned_data['choice'])
			avatar.primary = True
			avatar.save()
			updated = True
		if updated and notification:
			notification.send([request.user], 'avatar_updated', {'user': request.user, 'avatar': avatar})
			if friends:
				notification.send((x['friend'] for x in Friendship.objects.friends_for_user(request.user)),
					'avatar_friend_updated', {'user': request.user, 'avatar': avatar})

		return HttpResponseRedirect(next_override or _get_next(request))

	if request.method == 'POST':
		if "videotype" in request.POST:
			form = VideoForm(request.POST)
			if form.is_valid():
				form.save(client)
		else:
			result = process_form()
			if type(result) == str:
				error = result
			else:
				return result

	request.session['oauth_callback_redirect'] = reverse('import_facebook_photo')

	return render_to_response(
		'healers/settings/photo_edit.html',
		extra_context,
		context_instance=RequestContext(
			request,
			{
				'form': form,
				'VIDEO_TYPE_GALLERY': ClientVideo.VIDEO_TYPE_GALLERY,
				'gallery': gallery,
				'gallery_count': range(1, gallery.count()+1),
				'avatar': avatar,
				'avatars': avatars,
				'avatar_user': user,
				'username': username,
				'primary_avatar_form': primary_avatar_form,
				'next': next_override or _get_next(request),
				'error': error}
		)
	)


@user_authenticated
def schedule_enable(request):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	healer.scheduleVisibility = Healer.VISIBLE_EVERYONE
	healer.save()
	return redirect('availability')


@user_authenticated
def schedule_disable(request):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	healer.scheduleVisibility = Healer.VISIBLE_DISABLED
	healer.save()
	return redirect('availability')

class IframeTest(TemplateView):
	template_name = 'iframe_test.html'

	def dispatch(self, request, *args, **kwargs):
		if not settings.DEBUG:
			raise Http404

		return super(IframeTest, self).dispatch(request, *args, **kwargs)

def referrals_to_me(request, username):
	try:
		healer = Healer.objects.get(user__username__iexact=username)

		referring_users = [o['friend'] for o in Referrals.objects.referrals_to(healer.user)]
		healers = Healer.objects.filter(user__in=referring_users)
		referrals_to_me = []
		for h in healers:
			if not h.is_visible_to(request.user):
				h.user.private = True
			referrals_to_me.append(h.user)

		html = render_to_string('healers/referrals_to_me.html', {
			'referrals_to_me': referrals_to_me,
			'healer_name': unicode(healer.user.client),
			})

	except (Healer.DoesNotExist, ValueError):
		html = 'Could not find Healer ' + username

	return HttpResponse(html)


def healer_info(request, username):
	try:
		healer = Healer.objects.get(user__username__iexact=username)

		friendship, is_profile_visible, context = get_healer_info_context(healer, request)

		if not is_profile_visible:
			raise Healer.DoesNotExist

		context['info_only'] = True

		return render_to_response('healers/healer_sidebars.html', context, context_instance=RequestContext(request, {}, [friend_bar_processor]))

	except (Healer.DoesNotExist, ValueError):
		html = 'Could not find Healer ' + username

	return HttpResponse(html)


@user_authenticated
def appointment_history(request, template_name='healers/appointment_history.html', username=None):
	client = None
	if username:
		client = get_object_or_404(Client, user__username__iexact=username)
	appts = Appointment.get_appointments(request.user, 730, client)
	return render_to_response(template_name, {
		'appointment_list': appts,
		'client': client,
		}, context_instance=RequestContext(request))


@user_authenticated
def appointment_delete(request, id, start):
	appt = Appointment.objects.get(id=id)
	healer = get_healer(request.user, appt.healer.user.username)

	schedule_permission_result = check_schedule_permission(healer,
		location=appt.location)
	if schedule_permission_result is None:
		if appt.is_single():
			appt.cancel(healer.user)
		else:
			start_dt = datetime.utcfromtimestamp(int(start))
			appt.cancel_single(start_dt)
		return redirect(request.GET.get('redirect'))


#def ical(request, username):
#	try:
#		healer = Healer.objects.get(user__username__iexact=username)
#	except (Healer.DoesNotExist, ValueError):
#		return
#
#	appts = Appointment.objects.filter(healer__id = healer.id)
#
#	cal = vobject.iCalendar()
#	cal.add('method').value = 'PUBLISH'	 # IE/Outlook needs this
#	for appt in appts:
#		vevent = cal.add('vevent')
#		vevent.add('dtstart').value=appt.start #begin and end are python datetime objects
#		vevent.add('dtend').value=appt.end
#		vevent.add('summary').value=str(appt.client)
#		vevent.add('uid').value=str(appt.id)
#
#	icalstream = cal.serialize()
#	response = HttpResponse(icalstream, mimetype='text/calendar')
#	response['Filename'] = 'appointments.ics'  # IE needs this
#	response['Content-Disposition'] = 'attachment; filename=appointments.ics'
#	return response


@user_authenticated
def set_schedule_visibility(request, visibility, username):
	def get_redirect_page():
		referer = request.META.get('HTTP_REFERER', '')
		if 'settings' in referer:
			return reverse('schedule_settings', args=[username])
		if 'setup' in referer:
			return reverse('provider_setup', kwargs={'step': 12})
		return reverse('schedule', args=[username])

	healer = get_healer(request.user, username)

	new_visibility = -1

	if visibility == 'disabled':
		new_visibility = Healer.VISIBLE_DISABLED

	elif visibility == 'clients':
		new_visibility = Healer.VISIBLE_CLIENTS

	elif visibility == 'everyone':
		new_visibility = Healer.VISIBLE_EVERYONE

	if new_visibility > -1:
		healer.scheduleVisibility = new_visibility
		healer.save()

	return redirect(get_redirect_page())


@user_authenticated
def set_review_permission(request, permission):
	healer = get_object_or_404(Healer, user__id=request.user.id)

	new_permission = -1

	if permission == 'disabled':
		new_permission = Healer.VISIBLE_DISABLED

	elif permission == 'clients':
		new_permission = Healer.VISIBLE_CLIENTS

	elif permission == 'everyone':
		new_permission = Healer.VISIBLE_EVERYONE

	if new_permission > -1:
		healer.review_permission = new_permission
		healer.save()

	return redirect('review_list')


@login_required
def setup(request, step=0):
	healer = get_object_or_404(Healer, user__id=request.user.id)
	step = int(step)
	steps = Setup_Step_Names.get_steps(healer)
	ctx = {'prev_step': step - 1}
	if step != len(steps):
		ctx['next_step'] = step + 1

	request.step = step
	request.step_names = steps

	healer.setup_step = step
	healer.save()

	request.step_name = request.step_names[step - 1]

	if step == 0:
		template_name = 'healers/setup/welcome.html'
		ctx['hide_step_name'] = True

	elif step == 1:
		return location(request, template_name="healers/setup/location.html",
			redirect_url=reverse("provider_setup", args=(2,)), extra_context=ctx,
			account_setup=True)

	elif step == 2:
		modalities = list(Modality.objects_approved.get_with_unapproved(healer).filter(healer=healer))
		modalities.reverse()

		template_name = 'healers/setup/specialties.html'
		ctx.update({
			'modalities': modalities,
			'max_modalities': settings.MAX_MODALITIES_PER_HEALER,
			'username': request.user.username,
			'healer': healer,
		})

	elif step == 3:
		wcenter = is_wellness_center(healer)
		form_class = WellnessCenterOptionalInfoForm if wcenter else HealerOptionalInfoForm
		phones = ClientPhoneNumber.objects.filter(client=healer)

		if request.method == 'POST':
			form = form_class(request.POST)
			if form.is_valid():
				if phones:
					phones[0].number = form.cleaned_data['phone']
					phones[0].save()
				else:
					ClientPhoneNumber.objects.create(client=healer, number=form.cleaned_data['phone'])

				healer.years_in_practice = form.cleaned_data['years_in_practice']
				healer.website = form.cleaned_data['website']
				healer.facebook = form.cleaned_data['facebook']
				healer.twitter = form.cleaned_data['twitter']
				healer.google_plus = form.cleaned_data['google_plus']
				healer.linkedin = form.cleaned_data['linkedin']
				healer.yelp = form.cleaned_data['yelp']
				healer.save()
				return redirect('provider_setup', ctx['next_step'])

		else:
			form = form_class(initial={
				'first_name': healer.user.first_name,
				'last_name': healer.user.last_name,
				'phone': (phones[0].number if (len(phones) > 0) else ''),
				'years_in_practice': healer.years_in_practice,
				'website': healer.website,
				'facebook': healer.facebook,
				'twitter': healer.twitter,
				'google_plus': healer.google_plus,
				'linkedin': healer.linkedin,
				'yelp': healer.yelp,
				'ghp_notification_frequency': healer.ghp_notification_frequency,
				})

		template_name = 'healers/setup/optional_info.html'
		ctx.update({
			'form': form,
			'editing_self': True,
		})

	elif step == 4:
		request.session['oauth_callback_redirect'] = (reverse('import_facebook_photo') +
			'?next=' + reverse('provider_setup', kwargs={'step': 4}))

		template_name = 'healers/setup/photo.html'
		photo_id = None
		gallery = request.user.client.gallery_set.all().order_by('-id')
		if gallery.exists():
			photo_id = gallery[0].pk

		ctx.update({
			'photo_id': photo_id,
			'avatar_user': request.user,
			'username': request.user.username,
			'next': reverse('provider_setup', kwargs={'step': 4}),
		})

	elif step == 5:
		if request.method == 'POST':
			form = AboutClientForm(request.POST)
			if form.is_valid():
				healer.about = form.cleaned_data['about']
				healer.save()

				if request.POST.get('next', None):
					return redirect(request.POST.get('next', None))

		else:
			form = AboutClientForm(initial={
				'about': healer.about,
				})

		template_name = 'healers/setup/about.html'
		ctx['form'] = form

	elif step == 6:
		if is_wellness_center(healer):
			return friends(request, 'providers', extra_context=ctx,
				template_name='healers/setup/providers.html')

		return payments_settings(request, extra_context=ctx,
			template_name='healers/setup/payments_settings.html')

	elif step == 7:
		if is_wellness_center(healer):
			return payments_settings(request, extra_context=ctx,
				template_name='healers/setup/payments_settings.html')

		form_initial = {'message': healer.invite_message, 'invite_type': 'client'}
		join_request_form = ContactsJoinInviteRequestForm(initial=form_initial,
			user=request.user)

		template_name = 'healers/setup/recommend.html'
		ctx['join_request_form'] = join_request_form

	elif step == 8:
		import_type = request.GET.get('import_type', None)
		return blog_import(request, import_type=import_type, extra_context=ctx,
			template_name='healers/setup/blog_import.html', setup=True)
		# return render_to_response('healers/setup/preview_profile.html', {
		# 	'healer': healer
		# 	}, context_instance=RequestContext(request))

	elif step == 9:
		template_name = 'healers/setup/import_contacts.html'
		ctx['healer'] = healer

	elif step == 10:
		template_name = 'healers/setup/schedule_promo.html'
		ctx['healer'] = healer

	elif step == 11:
		ctx['redirect'] = reverse('provider_setup', args=(11,))
		return treatment_types(request,
			template_name='healers/setup/add_treatment_type.html',
			extra_context=ctx)

	elif step == 12:
		ctx['redirect'] = reverse('provider_setup', args=(ctx['next_step'],))
		return schedule_settings(request, extra_context=ctx,
			template_name='healers/setup/schedule_settings.html')

	elif step == 13:
		if request.user.is_active:
			return schedule(request, edit_availaibility=True, extra_context=ctx)
		template_name = 'healers/setup/schedule_email_not_confirmed.html'

	return render_to_response(template_name, ctx,
		context_instance=RequestContext(request))


def wcenter_request_permission(request, username):
	other_user = get_object_or_404(User, username__iexact=username)

	ctx = {
		'wellness_center': str(request.user.client),
		'wcenter_permission_url': request.build_absolute_uri(reverse('add_wellness_center_permission', args=[request.user.username]))
	}

	subject = render_to_string('healers/emails/existing_provider_request_permission_subject.txt', ctx)
	send_hs_mail(subject, 'healers/emails/existing_provider_request_permission_message.txt', ctx, request.user.email, [other_user.email])

	request.session['existing_provider_request_permission'] = "Your Request to Edit %s's Profile and Schedule has been sent successfully." % other_user.client

	return redirect('friends', 'providers')


@user_authenticated
def clients_visible_to_providers(request, state):
	wcenter = get_object_or_404(WellnessCenter, user=request.user)
	wcenter.clients_visible_to_providers = state == 'enable'
	wcenter.save()
	return redirect('friends', 'providers')


class SaveDiscountCode(HealerAuthenticated):
	def post(self, request, format=None):
		try:
			appointment_id = request.POST['appointment_id']
			discount_code_id = request.POST['discount_code_id']
		except:
			return HttpResponseBadRequest()

		def get_appointment():
			appointment = Appointment.objects.get(pk=appointment_id)
			get_healer(request.user, appointment.healer.user.username)  # check if healer has right to edit appointment
			return appointment

		def get_discount_code():
			if discount_code_id:
				return DiscountCode.objects.get(healer=self.healer, pk=discount_code_id)

		self.get_initial_data()
		appointment = get_appointment()
		appointment.discount_code = get_discount_code()
		appointment.save()

		return Response()


class AddTreatmentTypeLength(HealerAuthenticated):
	def post(self, request, format=None):
		try:
			data = QueryDict(request.POST['data'])
		except:
			return HttpResponseBadRequest()
		length_form = TreatmentTypeLengthForm(data)
		treatment_length = length_form.save(commit=False)
		treatment_length.treatment_type = TreatmentType.objects.get(pk=data['treatment_type_id'])
		treatment_length.save()
		return Response()


class LocationMap(APIView):
	def get(self, request, id, format=None):
		location = get_object_or_404(Location, pk=id)
		return Response({
			'x': location.point.x,
			'y': location.point.y,
			'title': location.title
		})


class NewClient(HealerAuthenticated):
	def post(self, request, format=None):
		self.get_initial_data()

		try:
			data = request.POST['data']
		except:
			return HttpResponseBadRequest()

		form = NewUserForm(QueryDict(data.encode('utf-8')))
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
				return None

			is_client = is_my_client(self.healer.user, user)

			# if client created by healer
			if not is_client:
				add_user_to_clients(self.healer.user, user)

			try:
				client = Client.objects.get(user=user)
			except ObjectDoesNotExist:
				client = Client(user=user)
				client.approval_rating = 100
				client.save()
			contact_info = client.get_contact_info(self.healer)
			if not contact_info:
				contact_info = ContactInfo.objects.create(
					healer=self.healer,
					client=client,
					first_name=user.first_name,
					last_name=user.last_name,
					address_line1=form.cleaned_data['address_line1'],
					address_line2=form.cleaned_data['address_line2'],
					postal_code=form.cleaned_data['postal_code'],
					city=form.cleaned_data['city'],
					state_province=form.cleaned_data['state_province'],
					country=form.cleaned_data['country']
				)
				contact_info.emails.add(ContactEmail(email=user.email))
			if form.cleaned_data['phone']:
				client.phone_numbers.add(ClientPhoneNumber(number=form.cleaned_data['phone']))
				contact_info.phone_numbers.add(ContactPhone(number=form.cleaned_data['phone']))
			if form.cleaned_data.get('referred_by', False):
				client.referred_by = form.cleaned_data['referred_by']
				client.save()

			client_entry = autocomplete_hs.views.build_client_entry(client)

			send_intake_form = form.cleaned_data.get('send_intake_form', False)
			if not user_exist:
				SiteJoinInvitation.objects.send_invitation(
					self.healer.user,
					form.cleaned_data['email'],
					message='',
					to_name='%s %s' % (user.first_name, user.last_name),
					send_intake_form=send_intake_form,
					intake_form_receiver_client=client)

			if user_exist and send_intake_form:
				self.healer.send_intake_form(client)
			return Response({'client': client_entry})
		else:
			error_list = ''
			error_elements = []
			for error in form.errors:
				error_elements.append('%s' % error)
				if error == '__all__':
					error_list += '%s' % str(form.errors[error])
				else:
					error_list += '%s: %s' % (error, str(form.errors[error]))
			return Response({'error_list': error_list, 'error_elements': error_elements})
