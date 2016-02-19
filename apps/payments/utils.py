import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib, timezone

import payments
import healers


def convert_tstamp(response, field_name=None):
	try:
		if field_name and response[field_name]:
			return datetime.datetime.fromtimestamp(
				response[field_name],
				timezone.utc
			)
		if not field_name:
			return datetime.datetime.fromtimestamp(
				response,
				timezone.utc
			)
	except KeyError:
		pass
	return None


def get_user_model():  # pragma: no cover
	try:
		# pylint: disable=E0611
		from django.contrib.auth import get_user_model as django_get_user_model
		return django_get_user_model()
	except ImportError:
		from django.contrib.auth.models import User
		return User


def load_path_attr(path):  # pragma: no cover
	i = path.rfind(".")
	module, attr = path[:i], path[i + 1:]
	try:
		mod = importlib.import_module(module)
	except ImportError, e:
		raise ImproperlyConfigured("Error importing %s: '%s'" % (module, e))
	try:
		attr = getattr(mod, attr)
	except AttributeError:
		raise ImproperlyConfigured("Module '%s' does not define a '%s'" % (
			module, attr)
		)
	return attr


def get_current_subscription(customer):
	return payments.models.CurrentSubscription.objects.get_or_create(customer=customer)[0]


def get_user_customer(user):
	try:
		return payments.models.Customer.objects.get(user=user)
	except payments.models.Customer.DoesNotExist:
		return payments.models.Customer.create(user)


def get_total_payment_for_center(payment, wc):
	payment *= len(healers.utils.get_healers_in_wcenter_with_schedule_editing_perm(wc))
	if payment > settings.PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT:
		return settings.PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT
	return payment
