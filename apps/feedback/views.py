from datetime import datetime

from rest_framework.response import Response

from django.conf import settings
from feedback.models import Feedback

from healers.utils import send_queued_mail
from account_hs.views import UserAuthenticated


class Submit(UserAuthenticated):
	def post(self, request, format=None):
		text = request.POST['text']
		if not text.strip():
			return Response('Please enter a comment in the box.')

		client = request.user.client
		feedback = Feedback(client=client, text=text, date=datetime.now())
		feedback.save()

		subject = "Feedback from %s %s" % (str(client), client.user.email)
		email_message = text

		send_queued_mail(subject, email_message, settings.SUPPORT_EMAIL, [settings.SUPPORT_EMAIL], reply_to=client.user.email)

		return Response(("<img src='%s/healersource/img/hs_logo_stripe.png' style='float:left; margin-right: 8px;' />"
								"<p><strong><em>Thanks so much for your suggestions!</em></strong></p>"
								"<p>We're constantly working to make HealerSource the best possible experience for you, so your feedback is most appreciated. </p>")
											% settings.STATIC_URL)
