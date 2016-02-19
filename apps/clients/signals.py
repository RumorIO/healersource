from emailconfirmation.models import EmailConfirmation
from emailconfirmation.signals import email_confirmed
from clients.mailchimp_ import mailchimp_create_member
from healers.models import is_healer


def email_confirmed_receiver(sender, instance=None, **kwargs):
	from account_hs.utils import after_signup
	user = kwargs.get("email_address").user
#	process_dummy_users(user)
	after_signup(user)

	if is_healer(user):
		mailchimp_create_member(user)

email_confirmed.connect(email_confirmed_receiver, sender=EmailConfirmation)
