from util import add_to_mailchimp

from django.conf import settings
from healers.threads import run_in_thread
import healers


@run_in_thread
def mailchimp_create_member(user):
	"""Add contact to appropriate mailchimp list."""
	add_to_mailchimp(settings.MAILCHIMP_LIST_ID, user.email, {'FNAME': user.first_name, 'LNAME': user.last_name, 'TYPE': healers.models.get_account_type(user)})
