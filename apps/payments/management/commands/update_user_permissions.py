from django.utils.timezone import datetime
from django.contrib.auth.models import User, Permission
from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q
from django.conf import settings

from healers.models import is_wellness_center, WellnessCenter
from healers.utils import get_healers_in_wcenter_with_schedule_editing_perm
from payments.models import Customer


class Command(BaseCommand):

	help = 'Update subscriptions status and user permissions.'

	def handle(self, *args, **options):
		"""Update subscriptions status and user permissions.

		Set whether it's active or not. Check all currently active subscriptions
		to set inactive status when period expires after cancellation. Clear
		permissions and add permission to users with active subscription.
		"""

		SCHEDULE_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_wcenter_schedule')
		NOTES_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_notes')
		BOOKING_PERMISSION_OBJECT = Permission.objects.get(codename='can_use_booking_no_fee')

		def get_original_users_with_permission(permission):
			return set(User.objects.filter(user_permissions=permission))

		def update_subscription_statuses(plan_type):
			def get_customers_with_active_subscription():
				status = {'current_subscription__%s_status' % plan_type: True}
				active = {'current_subscription__%s_active' % plan_type: True}
				return Customer.objects.filter(Q(**status) | Q(**active))

			for customer in get_customers_with_active_subscription():
				subscription = customer.get_subscription(plan_type)
				current_subscription = customer.current_subscription
				if (subscription is not None and subscription.status == 'active'):
					setattr(current_subscription, '%s_active' % plan_type, True)
				else:
					setattr(current_subscription, '%s_active' % plan_type, False)
				current_subscription.save()

		def get_users_with_active_subscription(plan_type):
			data = {'current_subscription__%s_active' % plan_type: True}
			return set([customer.user for customer in
					Customer.objects.filter(**data)])

		def get_current_users_with_schedule_permission():
			def get_wcenter_users_with_setting_each_provider_pays():
				return set([wc.user for wc in WellnessCenter.objects.filter(
					payment_schedule_setting=WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS)])

			def add_centers_with_active_trial_and_free_access():
				# trial
				centers = WellnessCenter.objects.exclude(schedule_trial_started_date=None)
				centers = [wc for wc in centers if wc.is_schedule_trial_active()]

				# free
				centers += list(WellnessCenter.objects.filter(user__username__in=settings.SCHEDULE_USERS_WITH_FREE_ACCESS))
				for wc in centers:
					users.add(wc.user)
					for healer in get_healers_in_wcenter_with_schedule_editing_perm(wc):
						users.add(healer.user)
			users = set()
			for user in get_users_with_active_subscription('schedule'):
				users.add(user)
				wc = is_wellness_center(user)
				if wc:
					for healer in get_healers_in_wcenter_with_schedule_editing_perm(wc):
						users.add(healer.user)

			add_centers_with_active_trial_and_free_access()
			users |= get_wcenter_users_with_setting_each_provider_pays()
			return users

		def get_current_users_with_notes_permission():
			def get_wcenter_users_with_setting_center_pays():
				return set([wc.user for wc in WellnessCenter.objects.filter(
					payment_schedule_setting=WellnessCenter.PAYMENT_CENTER_PAYS)])

			users = set(get_users_with_active_subscription('notes'))
			wcenters = get_wcenter_users_with_setting_center_pays()
			users |= wcenters
			for wc in wcenters:
				for healer in get_healers_in_wcenter_with_schedule_editing_perm(wc.client.healer):
					users.add(healer.user)

			return users

		def remove_schedule_permissions():
			users_to_remove = (original_users_with_schedule_permission -
				current_users_with_schedule_permission)
			for user in users_to_remove:
				user.user_permissions.remove(SCHEDULE_PERMISSION_OBJECT)
				print 'Schedule permission removed for %s: %s' % (user, datetime.now().date())

		def add_schedule_permissions():
			users_to_add = (current_users_with_schedule_permission -
				original_users_with_schedule_permission)
			for user in users_to_add:
				user.user_permissions.add(SCHEDULE_PERMISSION_OBJECT)
				print 'Schedule permission added for %s: %s' % (user, datetime.now().date())

		def remove_notes_permissions():
			users_to_remove = (original_users_with_notes_permission -
				current_users_with_notes_permission)
			for user in users_to_remove:
				user.user_permissions.remove(NOTES_PERMISSION_OBJECT)
				print 'Notes permission removed for %s: %s' % (user, datetime.now().date())

		def add_notes_permissions():
			users_to_add = (current_users_with_notes_permission -
				original_users_with_notes_permission)
			for user in users_to_add:
				user.user_permissions.add(NOTES_PERMISSION_OBJECT)
				print 'Notes permission added for %s: %s' % (user, datetime.now().date())

		def remove_booking_permissions():
			users_to_remove = (original_users_with_booking_permission -
				current_users_with_booking_permission)
			for user in users_to_remove:
				user.user_permissions.remove(BOOKING_PERMISSION_OBJECT)
				print 'Booking permission removed for %s: %s' % (user, datetime.now().date())

		def add_booking_permissions():
			users_to_add = (current_users_with_booking_permission -
				original_users_with_booking_permission)
			for user in users_to_add:
				user.user_permissions.add(BOOKING_PERMISSION_OBJECT)
				print 'Booking permission added for %s: %s' % (user, datetime.now().date())

		original_users_with_schedule_permission = get_original_users_with_permission(SCHEDULE_PERMISSION_OBJECT)
		update_subscription_statuses('schedule')
		current_users_with_schedule_permission = get_current_users_with_schedule_permission()

		remove_schedule_permissions()
		add_schedule_permissions()

		original_users_with_notes_permission = get_original_users_with_permission(NOTES_PERMISSION_OBJECT)
		update_subscription_statuses('notes')
		current_users_with_notes_permission = get_current_users_with_notes_permission()

		remove_notes_permissions()
		add_notes_permissions()

		original_users_with_booking_permission = get_original_users_with_permission(BOOKING_PERMISSION_OBJECT)
		update_subscription_statuses('booking')
		current_users_with_booking_permission = get_users_with_active_subscription('booking')

		remove_booking_permissions()
		add_booking_permissions()
