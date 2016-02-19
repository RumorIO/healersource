from django import forms
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from captcha.fields import CaptchaField
from healers.utils import send_hs_mail
from models import UnregisteredMessage
from util import get_name


class ComposeFormUnregistered(forms.Form):
	"""
		A simple form for messages from unregistered users.
	"""
	name = forms.CharField(
		label=_('Name'),
		max_length=30,
		widget=forms.TextInput()
	)

	email = forms.EmailField(
		label=_("E-mail"),
		widget=forms.TextInput()
	)
	note = forms.CharField(label="Message",
		widget=forms.Textarea(attrs={'cols': '40', 'rows': '5'}), required=False)

	msg_security_verification = CaptchaField(label='Security Verification')

	def save(self, sender):
		def save_message_date():
			message = UnregisteredMessage()
			message.save()

		lines = []
		first_name, last_name = get_name(self.cleaned_data['name'])
		lines.append("From: %s %s" % (first_name, last_name))

		if self.cleaned_data['email']:
			lines.append("Email: %s" % self.cleaned_data['email'])

		lines.append("")

		if self.cleaned_data['note']:
			lines.append("%s" % self.cleaned_data['note'])

		message = "\n".join(lines)
		ctx = {
			"SITE_NAME": settings.SITE_NAME,
			"sender": "%s %s" % (first_name, last_name),
			"message": message
			}

		subject = render_to_string("account/emails/send_message_unregistered_subject.txt", ctx)

		send_hs_mail(subject,
			"account/emails/send_message_unregistered_body.txt",
			ctx,
			settings.DEFAULT_FROM_EMAIL,
			[self.recipient])
		save_message_date()
