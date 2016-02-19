import stripe

from django.shortcuts import redirect

from oauth_access.models import UserAssociation
from oauth_access.callback import AuthenticationCallback

import healers
from .models import Payment


class StripeCallback(AuthenticationCallback):
	def __call__(self, request, access, token, publishable_key):
		if request.user.is_authenticated():
			user = request.user
			access.persist(user, token)
			user_assoc = UserAssociation.objects.get(user=user, service='stripe')
			user_assoc.identifier = publishable_key
			user_assoc.save()
			return redirect('stripe_connect_success')
		else:
			return redirect('login_page')

stripe_callback = StripeCallback()


def charge(card_token, user, amount, description):
	"""Charge card with amount (in dollars)."""
	def convert_to_cents(amount):
		return int(amount * 100)

	user_assoc = UserAssociation.objects.get(user=user, service='stripe')
	STRIPE_CONNECT_FEE_PERCENTAGE = 1

	try:
		if user.has_perm(healers.models.Healer.BOOKING_PERMISSION):
			application_fee = 0
		else:
			application_fee = convert_to_cents(round(amount * STRIPE_CONNECT_FEE_PERCENTAGE / 100))

		result = stripe.Charge.create(
			amount=convert_to_cents(amount),
			currency='usd',
			card=card_token,
			description=description,
			api_key=user_assoc.token,
			application_fee=application_fee
		)

		return {'id': result['id']}
	except stripe.error.StripeError, e:
		return {'error': str(e)}


def charge_for_appointment(appointment, card_token, amount):
	user = appointment.treatment_length.treatment_type.healer.user
	charge_result = charge(card_token, user, amount, 'HealerSource Appointment')
	if 'error' in charge_result:
		return charge_result['error']
	else:
		amount = int(amount * 100)
		Payment.objects.create(appointment=appointment, amount=amount,
			date=appointment.start_date, stripe_id=charge_result['id'])


def charge_for_appointments(appointments, card_token):
	def get_amount():
		amount = 0
		for appt in appointments:
			amount += appt.unpaid()
		return amount

	user = appointments[0].treatment_length.treatment_type.healer.user
	charge_result = charge(card_token, user, get_amount(), 'HealerSource Appointment')
	if 'error' in charge_result:
		return charge_result['error']
	else:
		for appt in appointments:
			amount = int(appt.unpaid() * 100)
			Payment.objects.create(appointment=appt, amount=amount,
				date=appt.start_date, stripe_id=charge_result['id'])


def create_card_token(customer, user):
	return stripe.Token.create(
		customer=customer.stripe_id,
		card=customer.card_stripe_id,
		api_key=UserAssociation.objects.get(user=user, service='stripe').token  # user's access token from the Stripe Connect flow
	)
