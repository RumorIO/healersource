# -*- coding: utf-8 -*-
from datetime import datetime
from random import random
import hashlib

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.loader import render_to_string
from emailconfirmation.models import EmailConfirmationManager, EmailConfirmation
from emailconfirmation.signals import email_confirmed
from account_hs.exceptions import EmailConfirmationExpiredError
from healers.utils import send_hs_mail
from util import absolute_url


class HtmlEmailConfirmationManager(EmailConfirmationManager):

	def confirm_email(self, confirmation_key):
		try:
			confirmation = self.get(confirmation_key=confirmation_key)
		except self.model.DoesNotExist:
			return None
		if not confirmation.key_expired():
			email_address = confirmation.email_address
			email_address.verified = True
			email_address.set_as_primary(conditional=True)
			email_address.save()
			email_confirmed.send(sender=self.model, email_address=email_address)
			return email_address
		else:
			raise EmailConfirmationExpiredError(confirmation)

	def send_confirmation(self, email_address, **kwargs):
		salt = hashlib.sha1(str(random())).hexdigest()[:5]
		confirmation_key = hashlib.sha1(salt + email_address.email).hexdigest()
		current_site = Site.objects.get_current()
		# check for the url with the dotted view path
		try:
			path = reverse("emailconfirmation.views.confirm_email",
				args=[confirmation_key])
		except NoReverseMatch:
			# or get path with named urlconf instead
			path = reverse(
				"emailconfirmation_confirm_email", args=[confirmation_key])
		activate_url = absolute_url(path)
		if 'next' in kwargs and kwargs['next']:
			activate_url += '?next=' + kwargs['next']
		context = {
			"user": email_address.user,
			"activate_url": activate_url,
			"email_template_header_url": activate_url,
			"current_site": current_site,
			"confirmation_key": confirmation_key,
			"recipient_email": email_address.email,
		}
		subject = render_to_string(
			"emailconfirmation/email_confirmation_subject.txt", context)
		# remove superfluous line breaks
		subject = "".join(subject.splitlines())
#		message = render_to_string(
#			"emailconfirmation/email_confirmation_message.txt", context)

		from_email = settings.DEFAULT_FROM_EMAIL
		recipient_list = [email_address.email]
#		message_html = message.replace("\n", "</br>")
		send_hs_mail(subject,
			"emailconfirmation/email_confirmation_message.txt",
			context, from_email, recipient_list)

		return self.create(
			email_address=email_address,
			sent=datetime.now(),
			confirmation_key=confirmation_key)

EmailConfirmation.add_to_class('objects', HtmlEmailConfirmationManager())
