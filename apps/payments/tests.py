import json
import stripe
from datetime import timedelta

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django_dynamic_fixture import G
from django.conf import settings
from django.test.utils import override_settings

from rest_framework.test import APIClient

from healers.models import (WellnessCenter, Healer, TreatmentType,
							TreatmentTypeLength)
from healers.tests import (WcentersBaseTest, create_test_time, create_timeslot,
	to_timestamp)
from healers.ajax import load_wcenter_providers, timeslot_new, timeslot_book
from client_notes.models import Note

from .utils import get_current_subscription, get_user_customer

if settings.TEST_INIT_PLANS:
	call_command('init_plans', payment_plans=settings.TEST_PAYMENTS_PLANS)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

"""
Other ajax functions which could be tested (they use schedule permission check):
- timeslot_update
- timeslot_delete
- appointment_new
- appointment_update
- appointment_delete_future
- appointment_delete
"""


class PaymentsBaseTest(WcentersBaseTest):
	def setUp(self):
		def remove_all_customers():
			customers = stripe.Customer.all()['data']
			for customer in customers:
				stripe.Customer.retrieve(customer.id).delete()

		def create_providers():
			self.provider1 = self.create_provider()
			self.provider2 = self.create_provider()
			map(self.make_active, [self.wc, self.provider1, self.provider2])

		def initialize_ajax_requests():
			self.rest_client_provider1 = APIClient()
			self.rest_client_provider1.force_authenticate(user=self.provider1.user)

			self.rest_client_provider2 = APIClient()
			self.rest_client_provider2.force_authenticate(user=self.provider2.user)

			self.rest_client_superuser = APIClient()
			self.rest_client_superuser.force_authenticate(user=User.objects.get(pk=1))

		def get_customers():
			self.customer = get_user_customer(self.wc.user)
			self.provider1_customer = get_user_customer(self.provider1.user)
			self.provider2_customer = get_user_customer(self.provider2.user)

		super(PaymentsBaseTest, self).setUp()
		self.location = self.create_location()[0]

		create_providers()
		initialize_ajax_requests()
		if settings.TEST_REMOVE_CUSTOMERS:
			remove_all_customers()
		get_customers()
		self.rest_client = APIClient()
		self.rest_client.force_authenticate(user=self.wc.user)

	def create_card(self, customer=None, number=4242424242424242):
		if customer is None:
			customer = self.customer
		card = {
			'address_city': None,
			'address_country': None,
			'address_line1': None,
			'address_line1_check': None,
			'address_line2': None,
			'address_state': None,
			'address_zip': None,
			'address_zip_check': None,
			'brand': 'Visa',
			'country': 'US',
			'cvc_check': 'pass',
			'exp_month': 12,
			'exp_year': 2017,
			'fingerprint': 'HZXwnDjZl581luCz',
			'funding': 'credit',
			'last4': '4242',
			'name': 'a1@dynamicfixture.com',
			'object': 'card',
			'type': 'Visa',
			'number': number,
		}
		try:
			customer.stripe_customer.cards.create(card=card)
			customer.save_card()
		except stripe.error.CardError, e:
			return e.json_body['error']['message']

	def has_schedule_perm(self, healer):
		return User.objects.get(pk=healer.user.id).has_perm(Healer.SCHEDULE_PERMISSION)

	def has_notes_perm(self, healer):
		return User.objects.get(pk=healer.user.id).has_perm(Healer.NOTES_PERMISSION)

	def clear_permissions(self):
		for user in User.objects.all():
			user.user_permissions.remove(self.get_schedule_permission_object())

	def cancel_subscription_immediately(self, customer):
		customer.get_subscription('schedule').delete()
		customer.current_subscription.schedule_status = False
		customer.current_subscription.save()

	def verify_permissions(self, permissions=[True, True, True], notes_permission_check=False):
		if notes_permission_check:
			permission_check = self.has_notes_perm
		else:
			permission_check = self.has_schedule_perm
		self.assertEqual(permission_check(self.wc), permissions[0])
		self.assertEqual(permission_check(self.provider1), permissions[1])
		self.assertEqual(permission_check(self.provider2), permissions[2])

	def save_account_settings(self, payment_schedule, payment_notes, payment_schedule_setting, rest_client=None):
		if rest_client is None:
			rest_client = self.rest_client
		response = rest_client.post(reverse('payments_save_account_settings'), {
			'payment_schedule': payment_schedule,
			'payment_notes': payment_notes,
			'payment_schedule_setting': payment_schedule_setting,
		})
		if response.content:
			return json.loads(response.content)


class PaymentsTest(PaymentsBaseTest):
	def test_add_card(self):
		self.assertFalse(self.wc.user.customer.can_charge())
		self.assertIsNone(self.create_card())
		self.assertTrue(self.wc.user.customer.can_charge())

	def test_add_card_error(self):
		self.assertEqual('Your card number is incorrect.',
			self.create_card(number=31231231212))

	def test_add_and_remove_card(self):
		self.assertIsNone(self.create_card())
		response = self.client.post(reverse('payments_remove_card'))
		self.assertIn('You do not have a card on file', response.content)


class PaymentsNotesTest(PaymentsBaseTest):
	def setUp(self):
		super(PaymentsNotesTest, self).setUp()

		for x in range(settings.NUMBER_OF_FREE_NOTES):
			G(Note, healer=self.wc, client=self.test_client, finalized_date=None)

	def test_no_card(self):
		result = self.save_account_settings(15, 15, WellnessCenter.PAYMENT_SCHEDULE_DISABLED)
		self.assertIn('Please add a card to change payment settings', result)

	def test_no_permission(self):
		response = self.rest_client.post(reverse('notes_create', args=[self.test_client.pk]))
		self.assertEqual({'error_type': 'no_notes_permission'},
			json.loads(response.content))

	def test_added_permission(self):
		self.create_card()
		result = self.save_account_settings(15, 15, WellnessCenter.PAYMENT_SCHEDULE_DISABLED)
		self.assertIsNone(result)
		self.rest_client.post(reverse('notes_create', args=[self.test_client.pk]))
		self.assertEqual(Note.objects.count(), settings.NUMBER_OF_FREE_NOTES + 1)


class PaymentsScheduleTest(PaymentsBaseTest):
	def test_center_pays_for_providers_no_card(self):
		result = self.save_account_settings(15, 0, WellnessCenter.PAYMENT_CENTER_PAYS)
		self.assertIn('Please add a card to change payment settings', result)

	def test_add_schedule_permission(self):
		self.add_schedule_permission(self.wc)
		self.assertTrue(self.has_schedule_perm(self.wc))

	def test_schedule(self):
		response = self.client.post(reverse('schedule'))
		self.assertNotIn('<div class="schedule-provider-select">', response.content)
		self.assertIn('Scheduling for Wellness Centers is a premium feature of HealerSource', response.content)

	@override_settings(PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT=45)
	def test_center_pays_more_than_max_payment(self):
		self.create_card()
		self.create_provider()
		self.create_provider()
		result = self.save_account_settings(15, 0, WellnessCenter.PAYMENT_CENTER_PAYS)
		self.assertIsNone(result)
		self.assertEqual(45, self.customer.get_total_charge_amount())


class PaymentsCenterPaysBaseTest(PaymentsBaseTest):
	def setUp(self):
		super(PaymentsCenterPaysBaseTest, self).setUp()
		self.create_card()
		result = self.save_account_settings(15, 0, WellnessCenter.PAYMENT_CENTER_PAYS)
		self.assertIsNone(result)


class CustomCenterPaymentTest(PaymentsBaseTest):
	def test_custom_center_payment(self):
		def save_account_settings():
			response = self.rest_client_superuser.post(reverse('payments_save_account_settings'), {
				'payment_schedule': 45,
				'user_id': self.wc.user.pk,
			})
			if response.content:
				return json.loads(response.content)

		self.create_card()
		result = save_account_settings()
		self.assertIsNone(result)
		wc = WellnessCenter.objects.get(pk=self.wc.pk)
		self.assertEqual(wc.payment_schedule_setting, WellnessCenter.PAYMENT_CENTER_PAYS)
		self.assertTrue(wc.user.customer.is_custom_schedule_plan)


# commented out max subscription payment
# class PaymentsCenterPaysTooMuchTest(PaymentsBaseTest):
# 	def test_center_pays_too_much(self):
# 		self.create_card()
# 		result = self.save_account_settings(settings.PAYMENTS_MAX_SUBSCRIPTION_PAYMENT + 5,
# 			0, WellnessCenter.PAYMENT_CENTER_PAYS)
# 		self.assertEqual(result, "Plan doesn't exist.")


class PaymentsCenterPaysUpdatePermissionsTest(PaymentsCenterPaysBaseTest):
	def test_center_pays_for_providers(self):
		self.clear_permissions()
		call_command('update_user_permissions')
		self.verify_permissions()
		self.verify_permissions(notes_permission_check=True)

	def test_cancel_subscription_center(self):
		self.cancel_subscription_immediately(self.customer)
		call_command('update_user_permissions')
		self.verify_permissions([False, False, False])

	def test_card_removal_error(self):
		response = self.client.post(reverse('payments_remove_card'))
		self.assertIn('You have to disable payments for &quot;schedule&quot; to remove your card.', response.content)


class PaymentsCenterPaysTest(PaymentsCenterPaysBaseTest):
	def test_center_pays_for_providers(self):
		self.verify_permissions()
		self.verify_permissions(notes_permission_check=True)

	def test_payment_history(self):
		response = self.client.get(reverse('payments_history'))
		self.assertEqual(response.status_code, 200)
		self.assertIn('Paid $30', response.content)

	def test_update_payment_schedule_for_center_less_providers(self):
		self.provider1.delete()
		call_command('update_payment_schedule_for_centers')
		self.assertEqual(15, self.customer.get_payment('schedule'))
		self.assertEqual(30, self.customer.get_total_charge_amount())
		self.assertEqual(15, self.customer.get_upcoming_invoices_total_amount())

	def test_update_payment_schedule_for_center_more_providers(self):
		self.create_provider()
		call_command('update_payment_schedule_for_centers')
		self.assertEqual(45, self.customer.get_payment('schedule'))
		self.assertEqual(30, self.customer.get_total_charge_amount())
		self.assertEqual(45 + 15,
			self.customer.get_upcoming_invoices_total_amount())


class PaymentsEachProviderPaysBaseTest(PaymentsBaseTest):
	def setUp(self):
		super(PaymentsEachProviderPaysBaseTest, self).setUp()
		# set up center setting - each provider pays, subscribe first provider

		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS)
		self.assertIsNone(result)
		self.login_with_provider(self.provider1.user)

		# add card
		self.create_card(self.provider1_customer)
		# payment center pays means healer pays in this case.
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_CENTER_PAYS, self.rest_client_provider1)
		self.assertIsNone(result)


class PaymentsEachProviderPaysUpdatePermissionsTest(PaymentsEachProviderPaysBaseTest):
	def test_each_center_providers_pays(self):
		self.clear_permissions()
		call_command('update_user_permissions')
		self.verify_permissions([True, True, False])

	def test_cancel_subscription_provider(self):
		self.cancel_subscription_immediately(self.provider1_customer)
		call_command('update_user_permissions')
		self.verify_permissions([True, False, False])

	def test_cancel_subscription_center(self):
		# cancel center subscription
		self.login_with_center()
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_SCHEDULE_DISABLED)
		self.assertIsNone(result)

		# cancel cancelled subscriptions immediately
		subscription = self.provider1_customer.get_subscription('schedule')
		if subscription.canceled_at is not None:
			subscription.delete()

		call_command('update_user_permissions')
		self.verify_permissions([False, False, False])


class PaymentsEachProviderPaysTest(PaymentsEachProviderPaysBaseTest):
	def test_each_center_provider_pays(self):
		self.verify_permissions([True, True, False])

	def test_cancel_subscription_provider(self):
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_SCHEDULE_DISABLED, self.rest_client_provider1)
		self.assertIsNone(result)
		self.assertFalse(get_current_subscription(
			self.provider1_customer).schedule_status)

	def test_cancel_subscription_center(self):
		self.login_with_center()
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_SCHEDULE_DISABLED)
		self.assertIsNone(result)
		self.assertFalse(get_current_subscription(
			self.provider1_customer).schedule_status)

	def test_change_to_center_pays(self):
		self.login_with_center()
		self.create_card()
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_CENTER_PAYS)
		self.assertIsNone(result)
		self.verify_permissions([True, True, True])


class PaymentsCenterPaysPermissionsTest(PaymentsCenterPaysBaseTest):
	def test_schedule_paid(self):
		response = self.client.post(reverse('schedule'))
		self.assertIn('<div class="schedule-provider-select">', response.content)
		self.assertEqual(len(response.context['providers']), 2)


class PaymentsEachProviderPaysPermissionsBaseTest(PaymentsEachProviderPaysBaseTest):
	def setUp(self):
		super(PaymentsEachProviderPaysPermissionsBaseTest, self).setUp()
		self.start = create_test_time() + timedelta(days=2)
		self.end = self.start + timedelta(hours=3)
		self.tt = G(TreatmentType, healer=self.wc)
		self.ttl = G(TreatmentTypeLength, treatment_type=self.tt, length=60)
		self.add_all_tts_to_providers([self.provider1, self.provider2])
		self.login_with_center()


class PaymentsEachProviderPaysPermissionsTest(PaymentsEachProviderPaysPermissionsBaseTest):
	def subscribe_provider2(self):
		self.login_with_provider(self.provider2.user)
		# add card
		self.create_card(self.provider2_customer)
		# payment center pays means healer pays in this case.
		result = self.save_account_settings(15,
			0, WellnessCenter.PAYMENT_CENTER_PAYS, self.rest_client_provider2)
		self.assertIsNone(result)

	def test_schedule_center(self):
		response = self.client.post(reverse('schedule'))
		self.assertIn('<div class="schedule-provider-select">', response.content)
		self.assertEqual(len(response.context['providers']), 1)
		self.assertEqual(response.context['providers_not_paid'][0]['name'],
			'Test_first6 Test_last6')

	def test_schedule_provider_not_paid(self):
		self.login_with_provider(self.provider2.user)
		response = self.client.post(reverse('schedule'))
		self.assertEqual(response.context['is_healers_schedule_not_paid'],
			'Booking at %s has been disabled because your account has not been paid.' % self.wc.user.client)

	def test_schedule_provider_paid(self):
		self.subscribe_provider2()
		response = self.client.post(reverse('schedule'))
		self.assertFalse(response.context['is_healers_schedule_not_paid'])

	def test_wcenter_providers_list(self):
		create_timeslot(self.provider1, self.start, self.end, location=self.location)
		create_timeslot(self.provider2, self.start, self.end, location=self.location)

		response = load_wcenter_providers(self.request, self.wc.pk, self.ttl.pk)
		self.assertEqual(self.wcenter_providers_list_providers_count(response), 1)

		self.subscribe_provider2()
		self.login_with_center()
		response = load_wcenter_providers(self.request, self.wc.pk, self.ttl.pk)
		self.assertEqual(self.wcenter_providers_list_providers_count(response), 2)

	def test_provider_locations(self):
		self.assertEqual(len(self.provider1.get_locations()), 1)
		self.assertFalse(self.provider2.get_locations())


class PaymentsEachProviderPaysTimeslotPermissionsTest(PaymentsEachProviderPaysPermissionsBaseTest):
	def setUp(self):
		super(PaymentsEachProviderPaysTimeslotPermissionsTest, self).setUp()
		# add a treatment type for each provider because it wouldn't create timeslots otherwise
		G(TreatmentType, healer=self.provider1)
		G(TreatmentType, healer=self.provider2)

	def create_timeslot(self, healer):
		return json.loads(timeslot_new(self.request,
			to_timestamp(self.start),
			to_timestamp(self.end),
			end_date=None,
			location_id=self.location.id,
			weekly=True,
			timeout_id=None,
			username=healer.user.username))

	def test_add_availability(self):
		response = self.create_timeslot(self.provider1)
		self.assertFalse(response['message'])
		response = self.create_timeslot(self.provider2)
		#self.assertEqual(response['message'], "Practitioner doesn't have permission to book appointments at the chosen location.")
		self.assertEqual(response['message'], "You don't have permission to edit the schedule")

	def test_book(self):
		def book(timeslot_id):
			start = create_test_time() + timedelta(days=2)
			return json.loads(timeslot_book(self.request, timeslot_id,
				to_timestamp(start), self.ttl.id, self.test_client.id, 'test',
				'', None))

		def get_timeslot_id(healer):
			return self.create_timeslot(healer)['slots'][0]['slot_id']

		timeslot_id1 = get_timeslot_id(self.provider1)
		self.add_schedule_permission(self.provider2)
		timeslot_id2 = get_timeslot_id(self.provider2)
		self.remove_schedule_permission(self.provider2)

		# book
		self.request.user = self.test_client.user
		response = book(timeslot_id1)
		self.assertEqual(response['title'], 'Appointment Scheduled')
		response = book(timeslot_id2)
		self.assertEqual(response['message'], "Practitioner doesn't have permission to book appointments at the chosen location.")
