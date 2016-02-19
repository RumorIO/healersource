import decimal

from django.conf import settings
from django.core.management.base import BaseCommand

import stripe


class Command(BaseCommand):

	help = "Make sure your Stripe account has the plans"

	def handle(self, payment_plans=None, *args, **options):
		stripe.api_key = settings.STRIPE_SECRET_KEY
		stripe.api_version = settings.STRIPE_API_VERSION

		if payment_plans is None:
			payment_plans = settings.PAYMENTS_PLANS
		for plan in payment_plans:
			if payment_plans[plan].get("stripe_plan_id"):
				price = payment_plans[plan]["price"]
				if isinstance(price, decimal.Decimal):
					amount = int(100 * price)
				else:
					amount = int(100 * decimal.Decimal(str(price)))

				try:
					stripe.Plan.create(
						amount=amount,
						interval=payment_plans[plan]["interval"],
						name=payment_plans[plan]["name"],
						currency=payment_plans[plan]["currency"],
						trial_period_days=payment_plans[plan].get(
							"trial_period_days"),
						id=payment_plans[plan].get("stripe_plan_id")
					)
					print "Plan created for {0}".format(plan)
				except stripe.error.InvalidRequestError, e:
					if str(e) == 'Plan already exists.':
						print 'Plan %s already exists.' % plan
						pass
