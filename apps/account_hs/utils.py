from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.conf import settings

from pinax.apps.account.utils import perform_login
from pinax.apps.account.models import EmailAddress
from friends.models import (Friendship, FriendshipInvitationHistory,
							FriendshipInvitation, JoinInvitation)

from clients.models import Client, SiteJoinInvitation
from contacts_hs.models import ContactInfo
from intake_forms.models import IntakeFormSentHistory
from healers.utils import invite_or_create_client_friendship
from healers.models import (Healer, WellnessCenter, Referrals, Clients,
							Appointment, is_healer)


def login_user(request, user):
	# nasty hack to get get_user to work in Django
	user.backend = settings.AUTHENTICATION_BACKENDS[0]
	perform_login(request, user)


def set_signup_source(user, request, is_phonegap=False):
	def get_signup_source():
		if is_phonegap:
			return Client.SIGNUP_SOURCE_APP
		elif request.session.get('notes_lp', False):
			return Client.SIGNUP_SOURCE_NOTES_LP

	client = Client.objects.get(user=user)
	signup_source = get_signup_source()
	if signup_source is not None:
		client.signup_source = signup_source
		client.save()


def set_phonegap_signup(user, is_phonegap):
	client = Client.objects.get(user=user)
	client.signup_source = Client.SIGNUP_SOURCE_APP
	client.save()


def post_signup_processing(user, is_ambassador, session):
	client = Client.objects.get(user=user)
	if is_ambassador:
		client.ambassador_program = True
	for param in settings.UTM_TRACKING_PARAMETERS:
		value = session.pop(param, None)
		setattr(client, param, value)
	client.save()


def get_or_create_email_address(user, email=None, verified=False, primary=False):
	if email is None:
		email = user.email
	try:
		email_address = EmailAddress.objects.get(user=user, email__iexact=email)
	except EmailAddress.DoesNotExist:
		email_address = EmailAddress.objects.create(user=user, email=email, verified=verified, primary=primary)
	return email_address


def after_signup(new_user, account_type=None, email_confirmed=True):
	def get_model_class():
		if account_type == 'healer':
			return Healer
		elif account_type == 'wellness_center':
			return WellnessCenter
		else:
			return Client

	def process_dummy_users(new_user):
		""" Move dummy user objects to new user, confirms appointments, remove dummy users """

		def copy_friendship(friendship_class, user, new_user):
			friends = friendship_class.objects.friends_for_user(user)
			for friend in friends:
				try:
					if friend['friendship'].from_user == user:
						friendship_class.objects.get_or_create(from_user=new_user, to_user=friend['friendship'].to_user)
					if friend['friendship'].to_user == user:
						friendship_class.objects.get_or_create(to_user=new_user, from_user=friend['friendship'].from_user)
				except IntegrityError:
					# friendship exists
					pass

		dummy_users = User.objects.filter(email__iexact=new_user.email).exclude(id=new_user.id)
		if len(dummy_users):
			# copy clients and referrals
			client = Client.objects.get(user=new_user)
			referred_by = []
			for user in dummy_users:
				copy_friendship(Clients, user, new_user)
				copy_friendship(Referrals, user, new_user)
				dummy_client = user.client
				if client.approval_rating < dummy_client.approval_rating:
					client.approval_rating = dummy_client.approval_rating
				if dummy_client.referred_by:
					referred_by.append(dummy_client.referred_by)
				dummy_client.phone_numbers.update(client=client)
				dummy_client.clientlocation_set.update(client=client)
				ContactInfo.objects.filter(client=dummy_client).update(client=client)
				IntakeFormSentHistory.objects.filter(client=dummy_client).update(client=client)

				#clear friendship invitation for dummy_user
				FriendshipInvitation.objects.filter(Q(from_user=user) | Q(to_user=user)).delete()
				FriendshipInvitationHistory.objects.filter(Q(from_user=user) | Q(to_user=user)).delete()
			#			SiteJoinInvitation.objects.filter(contact__email__iexact=user.email).delete()

			client.referred_by = ', '.join(referred_by)

			client.save()

			# confirm appointments
			dummy_user_ids = [u.id for u in dummy_users]
			client = Client.objects.get(user=new_user)
			appts = Appointment.objects.filter(client__user__id__in=dummy_user_ids)
			for appt in appts:
				if not appt.confirmed:
					if Appointment.check_for_auto_confirm(appt.healer, client):
						appt.confirm()
						appt.notify_created(client.user)
					else:
						appt.notify_requested(new_user)

				requested_friendships = []
				if appt.healer.id not in requested_friendships:
				#				request_friendship(client.user, appt.healer.user, ClientInvitation)
					invite_or_create_client_friendship(client.user, appt.healer.user)
					requested_friendships.append(appt.healer.id)

			appts.update(client=client)

			# remove all dummy users for this email
			dummy_users.delete()

	model_class = get_model_class()
	client = model_class.objects.get_or_create(user=new_user)[0]

	if not email_confirmed:
		return

	for join_invitation in SiteJoinInvitation.objects.filter(contact__email__iexact=new_user.email):
		ContactInfo.objects.filter(contact=join_invitation.contact).update(client=client)

		#is_from_site == unregistered booking
		if not join_invitation.is_from_site:
			if not is_healer(join_invitation.from_user):
				raise Healer.DoesNotExist

			if is_healer(new_user) and join_invitation.is_to_healer:
				FriendClass = Referrals
			else:
				FriendClass = Clients

			if join_invitation.create_friendship:
				friendship_exists = Friendship.objects.filter(
						from_user=join_invitation.from_user,
						to_user=new_user).exists()
				if not friendship_exists:
					FriendClass.objects.create(
						from_user=join_invitation.from_user,
						to_user=new_user)

			client.approval_rating = 100
			client.save()

			# fixes occurred problem.
			try:
				join_invitation.delete()
			except JoinInvitation.DoesNotExist:
				pass

	process_dummy_users(new_user)
