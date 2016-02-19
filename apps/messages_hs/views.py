from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import QueryDict, HttpResponseBadRequest
from django.template.loader import render_to_string

from captcha.models import CaptchaStore
from captcha.conf import settings as captcha_settings
from django_messages.forms import ComposeForm
from rest_framework.views import APIView
from rest_framework.response import Response

from util import get_errors, absolute_url
from healers.models import Healer
from healers.utils import send_hs_mail
from messages_hs.forms import ComposeFormUnregistered
from messages_hs.models import MessageExtra


class SendMessage(APIView):
	def post(self, request, format=None):
		try:
			data = request.POST['data'].encode('utf-8')
			source = request.POST.get('source', None)
		except:
			return HttpResponseBadRequest()

		if request.user.is_authenticated():
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

		if form.is_valid():
			m = form.save(sender=request.user)
			if source:
				MessageExtra.objects.create(message=m[0], source=source)
	#		request.user.message_set.create(
	#			message=_(u"Message successfully sent."))
	#		success_url = reverse('messages_inbox')
	#		if request.GET.has_key('next'):
	#			success_url = request.GET['next']

		#update captcha
		challenge, captcha_response = captcha_settings.get_challenge()()
		store = CaptchaStore.objects.create(challenge=challenge, response=captcha_response)
		errors, error_elements, _ = get_errors(form)

		return Response({'errors': errors,
						'error_elements': error_elements,
						'captcha': {
							'img': reverse('captcha-image', kwargs=dict(key=store.hashkey)),
							'code': store.hashkey}})

	#def new_message_form_processor(request):
	#
	#	if request.user.is_authenticated():
	#		new_message_form = ComposeForm()
	#	else:
	#		new_message_form = None
	#
	#	return { "new_message_form" : new_message_form }
