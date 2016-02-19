from clients.models import Client
from ambassador.settings import COOKIE_NAME


def set_ambassador(client_user=None, ambassador_user=None, cookies=None):
	"""
	Set ambassador and ambassdor_plan for Client.
	- for signup, ambassador from cookie
	- for signup, ambassador from referral
	- for provider created by wcenter
	"""
	if not client_user:
		return

	try:
		client = client_user.client

		if ambassador_user:
			ambassador = ambassador_user.client
		elif cookies and COOKIE_NAME in cookies:
			ambassador_username = cookies.pop(COOKIE_NAME)
			ambassador = Client.objects.get(
					user__username__exact=ambassador_username)
		else:
			return
	except Client.DoesNotExist:
		# no client or ambassador
		return

	if not ambassador.ambassador_plan:
		return

	client.ambassador = ambassador
	client.ambassador_plan = ambassador.ambassador_plan
	client.save()
