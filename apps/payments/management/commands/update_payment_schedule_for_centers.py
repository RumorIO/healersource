from django.core.management.base import BaseCommand

from healers.models import WellnessCenter

from payments.utils import get_total_payment_for_center


class Command(BaseCommand):

	help = 'Updates payment schedule for centers if number of providers has changed'

	def handle(self, *args, **options):
		"""Update payment schedule for centers if number of providers has changed."""
		def is_prorated(new_payment, current_payment):
			return new_payment > current_payment

		PLAN_TYPE = 'schedule'
		wcenters = WellnessCenter.objects.filter(
			payment_schedule_setting=WellnessCenter.PAYMENT_CENTER_PAYS)
		for wc in wcenters:
			customer = wc.user.customer
			payment = get_total_payment_for_center(customer.payment_schedule, wc)
			plan_id = customer.get_plan_id(PLAN_TYPE, payment)
			subscription = customer.get_subscription(PLAN_TYPE)
			if subscription is not None:
				prorate = is_prorated(payment, customer.get_payment(
					PLAN_TYPE, subscription))
				customer.update_subscription(subscription, plan_id, prorate)
