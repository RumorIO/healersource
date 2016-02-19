from django.conf import settings
#from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax
from captcha.models import CaptchaStore
from captcha.conf import settings as captcha_settings
#from healers.ajax import login_required_ajax
from healers.models import Healer
from healers.utils import send_hs_mail
from messages_hs.forms import ComposeFormUnregistered
from messages_hs.models import MessageExtra
from django_messages.forms import ComposeForm
from util import absolute_url


@dajaxice_register
def send_message(request, data, is_registered, source=None):
	dajax = Dajax()

#	sender = request.user
	if is_registered:
		form = ComposeForm(QueryDict(data))
		if form.is_valid():
			sender = str(request.user.client)

			lines = []
			lines.append("From: %s" % sender)
			lines.append("Email: %s" % request.user.email)
			lines.append("")
			lines.append("Subject: %s" % form.cleaned_data['subject'])
			lines.append("")
			lines.append(form.cleaned_data['body'])

			message = "\n".join(lines)

			ctx = {
				"SITE_NAME": settings.SITE_NAME,
				"sender": sender,
				"message": message,
				"reply_url": absolute_url(reverse('messages_inbox'))
			}

			subject = render_to_string("account/emails/send_message_unregistered_subject.txt", ctx)

			send_hs_mail(subject, "account/emails/send_message_unregistered_body.txt", ctx, settings.DEFAULT_FROM_EMAIL, [form.cleaned_data['recipient'][0].email])

	else:
		qd = QueryDict(data)

		try:
			recipient = Healer.objects.get(user__username__iexact=qd['recipient_username'])
		except Healer.DoesNotExist:
			return

		form = ComposeFormUnregistered(qd)
		form.recipient = recipient.user.email

	dajax.remove_css_class('#new_message_form input','error')
	dajax.remove_css_class('#new_message_form textarea','error')
	if form.is_valid():
		m = form.save(sender=request.user)
		if source:
			MessageExtra.objects.create(message=m[0], source=source)
#		request.user.message_set.create(
#			message=_(u"Message successfully sent."))
#		success_url = reverse('messages_inbox')
#		if request.GET.has_key('next'):
#			success_url = request.GET['next']

		dajax.script("new_message_success();")

	else:
		for error in form.errors:
			if error == "captcha":
				css_class = '#new_message_form #id_%s_1'
			else:
				css_class = '#new_message_form #id_%s'
			dajax.add_css_class(css_class % error,'error')

	#update captcha
	challenge, response = captcha_settings.get_challenge()()
	store = CaptchaStore.objects.create(challenge=challenge, response=response)
	dajax.assign('img.captcha', 'src', reverse('captcha-image',kwargs=dict(key=store.hashkey)))
	dajax.assign('#id_msg_security_verification_0', 'value', store.hashkey)
	dajax.assign('#id_msg_security_verification_1', 'value', '')

	return dajax.json()

#def new_message_form_processor(request):
#
#	if request.user.is_authenticated():
#		new_message_form = ComposeForm()
#	else:
#		new_message_form = None
#
#	return { "new_message_form" : new_message_form }