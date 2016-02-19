from datetime import datetime, timedelta
import stripe
import json

from django.http import Http404
from django.conf import settings
from django.core.mail import mail_admins
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.contrib.auth.models import User, Permission
from django.shortcuts import render_to_response, redirect, get_object_or_404

from rest_framework.response import Response
from oauth_access.models import UserAssociation

from account_hs.authentication import user_authenticated
from account_hs.views import UserAuthenticated
from clients.models import Client
import healers
from healers.models import (WellnessCenter, Healer, Appointment, is_healer,
							is_wellness_center)
from healers.views import HealerAuthenticated
from autocomplete_hs.views import autocomplete_all_clients

from .utils import (get_user_customer, get_current_subscription,
	get_total_payment_for_center)
from .stripe_connect import charge_for_appointments, create_card_token
from .forms import BookingPaymentsSettingsForm

# from django.core.exceptions import ObjectDoesNotExist
# from django.http import HttpResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# from django.template.loader import render_to_string
# from .forms import PlanForm
# from . import settings as app_settings
# from .models import (
# 	Customer,
# 	CurrentSubscription,
# 	PaymentEvent,
# 	PaymentEventProcessingException
# )

stripe.api_version = settings.STRIPE_API_VERSION
DATE_FORMAT = '%m/%d/%Y'


class HistoryView(TemplateView):
	template_name = 'payments/history.html'


@user_authenticated
def remove_card(request):
	def check_all_payments_disabled():
		for plan_type in settings.PLAN_TYPES:
			current_subscription = get_current_subscription(customer)
			if getattr(current_subscription, '%s_status' % plan_type):
				return 'You have to disable payments for "%s" to remove your card.' % plan_type

	customer = get_user_customer(request.user)
	error = check_all_payments_disabled()
	if error is None:
		customer.remove_card()

	if is_healer(request.user):
		return healers.views.account(request, error)
	else:
		return redirect('clients_profile')


@user_authenticated
def stripe_connect_success(request):
	stripe_success_redirect = request.session.pop('stripe_success_redirect', None)
	if stripe_success_redirect is not None:
		return redirect(stripe_success_redirect)

	request.session['stripe_success_redirect'] = 'stripe_connect_payments'
	return healers.views.payments_settings(request,
		template_name='payments/payments_success.html')


@user_authenticated
def disable_stripe_connect(request):
	UserAssociation.objects.filter(user=request.user, service='stripe').delete()
	healer = is_healer(request.user)
	healer.gift_certificates_enabled = False
	healer.booking_healersource_fee = Healer.BOOKING_HEALERSOURCE_FEE_PERCENTAGE
	healer.save()
	return healers.views.payments_settings(request,
		message='Stripe Connect has been disabled.')


def get_booking_payments_settings_form(healer):
	return BookingPaymentsSettingsForm(
		{'booking_payment_requirement': healer.booking_payment_requirement,
		'booking_healersource_fee': healer.booking_healersource_fee})


@user_authenticated
def stripe_connect_payments(request):
	healer = get_object_or_404(Healer, user=request.user)
	date_end = healer.get_local_day()
	date_start = date_end - timedelta(days=settings.STRIPE_CONNECT_PAYMENTS_NUMBER_OF_DAYS)
	return render_to_response('payments/stripe_connect_payments.html',
		{'clients': autocomplete_all_clients(request),
			'discount_codes': healer.discount_codes.all(),
			'date_start': date_start,
			'date_end': date_end,
			'STRIPE_APP_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
			'STRIPE_CONNECT_LINK': settings.STRIPE_CONNECT_LINK,
			'form': get_booking_payments_settings_form(healer)
			},
		context_instance=RequestContext(request))


def convert_to_date(date):
	return datetime.strptime(date, DATE_FORMAT).date()


class StripeConnectPayments(HealerAuthenticated):
	def get(self, request, format=None):
		def get_client():
			client_id = request.GET.get('client', False)
			if client_id:
				return Client.objects.get(pk=client_id)

		def get_date(date):
			date = request.GET.get(date, False)
			if date:
				return convert_to_date(date)
		try:
			start_date = get_date('start_date')
			end_date = get_date('end_date')
		except ValueError:
			return Response({'error': 'The date format should be %s' % DATE_FORMAT.lower().replace('%', '')})

		appts = Appointment.get_appointments(request.user,
			settings.STRIPE_CONNECT_PAYMENTS_NUMBER_OF_DAYS, get_client(),
			start_date, end_date)
		html = render_to_string('payments/stripe_connect_payments_table.html',
			RequestContext(request, {'appointment_list': appts}))
		return Response({'html': html})


def get_appointment(user, appointment_id, appointment_date):
	"""Get appointment and checks if a user can access it."""
	def check_access():
		healer = user.client.healer
		if healer != appointment.healer and healer != appointment.treatment_length.treatment_type.healer:
			raise Http404
	appointment = Appointment.objects.get(pk=appointment_id)
	check_access()
	appointment.start_date = convert_to_date(appointment_date)
	return appointment


class AppointmentPayment(HealerAuthenticated):
	def get_initial_data(self):
		self.appointment = get_appointment(self.request.user,
			self.request.POST['id'], self.request.POST['date'])


class MarkPaid(AppointmentPayment):
	def post(self, request, format=None):
		self.get_initial_data()
		self.appointment.mark_paid()
		return Response()


class MarkUnpaid(AppointmentPayment):
	def post(self, request, format=None):
		self.get_initial_data()
		self.appointment.mark_unpaid()
		return Response()


class ClientAppointments(AppointmentPayment):
	"""Client's Unpaid Appointments."""
	def post(self, request, format=None):
		self.get_initial_data()

		client = self.appointment.client
		customer = get_user_customer(client.user)
		if not customer.can_charge():
			card_token = request.POST.get('card_token', None)
			if card_token is None:
				return Response({'has_card': False, 'client_email': client.user.email})
			else:
				try:
					customer.update_card(card_token)
				except stripe.CardError, e:
					return Response({'error': e.message})

		# appts = healers.models.Appointment.get_appointments(request.user,
		# 	365, self.appointment.client, only_unpaid=True)

		appts = Appointment.get_appointments(request.user,
			365, self.appointment.client, only_unpaid=True, end_date=request.user.client.healer.get_local_day() + timedelta(days=7))
		response = {'has_card': True,
			'appointments': [{'id': appt.pk, 'date': appt.start_date.strftime(DATE_FORMAT)} for appt in appts]}
		if len(appts) > 1:
			response['html'] = render_to_string('payments/stripe_connect_client_appointments.html',
				{'appointments': appts})
		return Response(response)


class Charge(AppointmentPayment):
	def post(self, request, format=None):
		def get_appointments():
			appointments = json.loads(self.request.POST['appointments'])
			return [get_appointment(request.user, appt['id'], appt['date']) for appt in appointments]

		appointments = get_appointments()
		customer = get_user_customer(appointments[0].client.user)
		try:
			card_token = create_card_token(customer,
				appointments[0].treatment_length.treatment_type.healer.user)
		except stripe.error.StripeError, e:
			return Response({'error': e.message})
		charge_result = charge_for_appointments(appointments, card_token)
		if charge_result is not None:
			return Response({'error': charge_result})
		return Response()


class SaveCard(UserAuthenticated):
	def post(self, request, format=None):
		customer = get_user_customer(request.user)
		try:
			send_invoice = customer.card_fingerprint == ''
			customer.update_card(request.POST['stripe_token'])
			if send_invoice:
				customer.send_invoice()
			customer.retry_unpaid_invoices()
			html = render_to_string('payments/card_settings_history.html',
				{'user': request.user,
				'history': request.POST.get('history', False)})
			result = {'html': html}
		except stripe.CardError, e:
			result = {'error': e.message}
		return Response(result)


def process_subscription(user, plan_type, payment, wc=False, is_custom_schedule_plan=False):
	"""Return error (str) on error and None on success."""
	customer = get_user_customer(user)  # initialize customer
	if getattr(customer, 'payment_%s' % plan_type) != payment:
		current_subscription = get_current_subscription(customer)
		if payment > 0:
			if customer.can_charge():
				if plan_type == 'schedule' and wc and not is_custom_schedule_plan:
					payment = get_total_payment_for_center(payment, wc)

				# commented out max subscription payment
				# if payment > settings.PAYMENTS_MAX_SUBSCRIPTION_PAYMENT:
				# 	mail_admins("Plan doesn't exist.", '%s - %d' % (user.username, payment))
				# 	return "Plan doesn't exist."

				try:
					customer.subscribe(plan_type, payment)
				except stripe.error.StripeError, e:
					return str(e)
				setattr(current_subscription, '%s_status' % plan_type, True)

				SCHEDULE_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_wcenter_schedule')
				NOTES_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_notes')
				BOOKING_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_booking_no_fee')

				# add permissions
				if plan_type == 'schedule':
					permission = SCHEDULE_PERMISSION_OBJECT
				elif plan_type == 'notes':
					permission = NOTES_PERMISSION_OBJECT
				elif plan_type == 'booking':
					permission = BOOKING_PERMISSION_OBJECT
				user.user_permissions.add(permission)
				if plan_type == 'schedule' and wc:
					# Free Notes for center who pays
					user.user_permissions.add(NOTES_PERMISSION_OBJECT)
					for healer in healers.utils.get_healers_in_wcenter_with_schedule_editing_perm(wc):
						healer.user.user_permissions.add(permission)
						# Free Notes for center clients
						healer.user.user_permissions.add(NOTES_PERMISSION_OBJECT)
			else:
				if plan_type == 'booking':
					action = 'checkout(undefined, checkout_callback_payments_settings);'
				else:
					action = 'checkout();'
				return 'Please add a card to change payment settings: <a href="javascript:void(0);" onclick="%s">Click Here</a>.' % action
		else:
			try:
				customer.cancel(plan_type)
			except stripe.error.StripeError, e:
				return e.message
			setattr(current_subscription, '%s_status' % plan_type, False)
		current_subscription.save()


class SaveAccountSettings(HealerAuthenticated):
	def post(self, request, format=None):
		def set_payment_schedule_to_0_for_healers_in_center():
			wcenter_healers = healers.utils.get_healers_in_wcenter_with_schedule_editing_perm(wc)
			for h in wcenter_healers:
				customer = get_user_customer(h.user)
				customer.payment_schedule = 0
				customer.save()
				try:
					customer.cancel('schedule')
				except stripe.error.StripeError as e:
					mail_admins('Error deleting schedule subscription', 'Error deleting schedule subscription for %s - %s' % (customer, str(e)))
					pass
				current_subscription = get_current_subscription(customer)
				current_subscription.schedule_status = False
				current_subscription.save()

		self.get_initial_data()

		SCHEDULE_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_wcenter_schedule')

		payment_schedule = int(request.POST['payment_schedule'])
		is_custom_schedule_plan = request.user.is_superuser and 'user_id' in request.POST

		if is_custom_schedule_plan:
			payment_schedule_setting = WellnessCenter.PAYMENT_CENTER_PAYS
			user = User.objects.get(pk=request.POST['user_id'])
			customer = user.customer
			wc = WellnessCenter.objects.get(user=user)
		else:
			payment_schedule_setting = int(request.POST['payment_schedule_setting'])
			payment_notes = int(request.POST['payment_notes'])
			user = request.user
			customer = get_user_customer(user)  # initialize customer
			wc = is_wellness_center(self.healer)

			if payment_schedule_setting in [WellnessCenter.PAYMENT_SCHEDULE_DISABLED,
					WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS]:
				payment_schedule = 0
				if payment_schedule_setting == WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS:
					user.user_permissions.add(SCHEDULE_PERMISSION_OBJECT)

		errors = []
		error = process_subscription(user, 'schedule', payment_schedule, wc, is_custom_schedule_plan)
		if error is None:
			customer.payment_schedule = payment_schedule
			customer.is_custom_schedule_plan = is_custom_schedule_plan
			customer.save()
			if wc:
				wc = WellnessCenter.objects.get(user=wc.user)  # Refresh WellnessCenter record
				wc.payment_schedule_setting = payment_schedule_setting
				wc.save()
				if payment_schedule_setting in [WellnessCenter.PAYMENT_SCHEDULE_DISABLED,
						WellnessCenter.PAYMENT_CENTER_PAYS]:
					set_payment_schedule_to_0_for_healers_in_center()
		else:
			errors.append(error)

		if not is_custom_schedule_plan:
			error = process_subscription(user, 'notes', payment_notes, wc)
			if error is None:
				if customer.payment_notes != payment_notes:
					customer.payment_notes = payment_notes
					customer.save()
			else:
				errors.append(error)

		if errors:
			error = '<br>'.join(errors)

		return Response(error)


# def _ajax_response(request, template, **kwargs):
# 	response = {
# 		"html": render_to_string(
# 			template,
# 			RequestContext(request, kwargs)
# 		)
# 	}
# 	if "location" in kwargs:
# 		response.update({"location": kwargs["location"]})
# 	return HttpResponse(json.dumps(response), content_type="application/json")


# class PaymentsContextMixin(object):
# 	def get_context_data(self, **kwargs):
# 		context = super(PaymentsContextMixin, self).get_context_data(**kwargs)
# 		context.update({
# 			'STRIPE_PUBLIC_KEY': app_settings.STRIPE_PUBLIC_KEY,
# 			'PLAN_CHOICES': app_settings.PLAN_CHOICES,
# 			'PAYMENT_PLANS': app_settings.PAYMENTS_PLANS
# 		})
# 		return context


# @require_POST
# @user_authenticated
# def change_plan(request):
# 	form = PlanForm(request.POST)
# 	try:
# 		current_plan = request.user.customer.current_subscription.plan
# 	except CurrentSubscription.DoesNotExist:
# 		current_plan = None
# 	if form.is_valid():
# 		try:
# 			request.user.customer.subscribe(form.cleaned_data["plan"])
# 			data = {
# 				"form": PlanForm(initial={"plan": form.cleaned_data["plan"]})
# 			}
# 		except stripe.error.StripeError, e:
# 			data = {
# 				"form": PlanForm(initial={"plan": current_plan}),
# 				"error": e.message
# 			}
# 	else:
# 		data = {
# 			"form": form
# 		}
# 	return _ajax_response(request, "payments/_change_plan_form.html", **data)


# @require_POST
# @user_authenticated
# def subscribe(request, form_class=PlanForm):
# 	data = {"plans": settings.PAYMENTS_PLANS}
# 	form = form_class(request.POST)
# 	if form.is_valid():
# 		try:
# 			try:
# 				customer = request.user.customer
# 			except ObjectDoesNotExist:
# 				customer = Customer.create(request.user)
# 			if request.POST.get("stripe_token"):
# 				customer.update_card(request.POST.get("stripe_token"))
# 			customer.subscribe(form.cleaned_data["plan"])
# 			data["form"] = form_class()
# 			data["location"] = reverse("payments_history")
# 		except stripe.error.StripeError as e:
# 			data["form"] = form
# 			try:
# 				data["error"] = e.args[0]
# 			except IndexError:
# 				data["error"] = "Unknown error"
# 	else:
# 		data["error"] = form.errors
# 		data["form"] = form
# 	return _ajax_response(request, "payments/_subscribe_form.html", **data)


# @require_POST
# @user_authenticated
# def cancel(request):
# 	try:
# 		request.user.customer.cancel()
# 		data = {}
# 	except stripe.error.StripeError, e:
# 		data = {"error": str(e)}
# 	return _ajax_response(request, "payments/_cancel_form.html", **data)


# @csrf_exempt
# @require_POST
# def webhook(request):
# 	data = json.loads(request.body)
# 	if Event.objects.filter(stripe_id=data["id"]).exists():
# 		EventProcessingException.objects.create(
# 			data=data,
# 			message="Duplicate event record",
# 			traceback=""
# 		)
# 	else:
# 		event = Event.objects.create(
# 			stripe_id=data["id"],
# 			kind=data["type"],
# 			livemode=data["livemode"],
# 			webhook_message=data
# 		)
# 		event.validate()
# 		event.process()
# 	return HttpResponse()


# class SubscribeView(PaymentsContextMixin, TemplateView):
# 	template_name = "payments/subscribe.html"

# 	def get_context_data(self, **kwargs):
# 		context = super(SubscribeView, self).get_context_data(**kwargs)
# 		context.update({
# 			"form": PlanForm
# 		})
# 		return context


# class CancelView(PaymentsContextMixin, TemplateView):
# 	template_name = "payments/cancel.html"


# class ChangePlanView(SubscribeView):
# 	template_name = "payments/change_plan.html"
