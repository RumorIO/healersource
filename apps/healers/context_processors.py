from datetime import timedelta

from django.conf import settings

from about.views import get_city_select_code
from clients.models import Client
from healers.forms import HealerSearchForm
from healers.models import Appointment, ClientInvitation, Healer, is_healer, is_wellness_center
from healers.utils import get_healers_in_wcenter_with_schedule_editing_perm, get_wcenter_unconfirmed_appts


def running_local_processor(request):
	return { 'RUNNING_LOCAL': settings.RUNNING_LOCAL }


def find_healer_processor(request):
	session = request.session.get('search_state', None)
	city_select_code = 0
	if session is not None:
		city_select_code = get_city_select_code(session)

	form = HealerSearchForm(initial=session)
	return {
		'search_healer_form': form,
		'city_select_code': city_select_code}


def is_healer_processor(request):
	healer = False
	beta_tester = True

	func = getattr(request.user, "client", None)
	if func:
		healer = is_healer(request.user)
#		beta_tester = request.user.client.beta_tester
	return {'is_healer': healer, 'is_beta_tester': beta_tester,
			'is_wellness_center': is_wellness_center(healer),
			'healers_in_wcenter_with_schedule_perm': get_healers_in_wcenter_with_schedule_editing_perm(healer),
			'is_stripe_connect_beta_tester': True,  #request.user.username in settings.STRIPE_CONNECT_BETA_USERS
			'is_gift_certificates_beta_tester': True  # request.user.username in settings.GIFT_CERTIFICATES_BETA_USERS
		}


def unconfirmed_appointments_processor(request):
	try:
		client = request.user.client

		try:
			healer = client.healer
			wcenter = is_wellness_center(healer)
			if wcenter:
				appts = get_wcenter_unconfirmed_appts(wcenter)
			else:
				appts = Appointment.objects.get_active(healer).filter(confirmed=False)

			number_of_unconfirmed_appts = appts.count()

		except Healer.DoesNotExist:
			number_of_unconfirmed_appts = Appointment.objects.without_relations()\
																			.filter(client=request.user.client)\
																			.filter_by_date(settings.GET_NOW().date() - timedelta(days=1))\
																			.order_by('start_date')\
																			.count()
	except (Client.DoesNotExist, AttributeError):
		number_of_unconfirmed_appts = 0

	return {'number_of_unconfirmed_appts': number_of_unconfirmed_appts}

def invitations_count(request, context_variable_name, FriendClass):
	if request.user.is_authenticated():
#		count = FriendClass.objects.filter(
#				to_user = request.user,
#				status = "2"
#			).count()
		return {
			context_variable_name: FriendClass.objects.filter(
				to_user = request.user,
				status = "2"
			).count()
		}
	else:
		return {}

def client_invitations_processor(request):
	return invitations_count(request, "client_invitations_count", ClientInvitation)

#def referral_invitations_processor(request):
#	return invitations_count(request, "referral_invitations_count", ReferralInvitation)

