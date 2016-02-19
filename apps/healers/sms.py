from django.conf import settings
from twilio.rest import TwilioRestClient
from healers.threads import run_in_thread

@run_in_thread
def send_sms(to, body):
	client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
	message_content = {'body': body.strip(),
	                   'to': to,
	                   'from_':settings.TWILIO_PHONE_NUMBER}
	if settings.DEBUG:
		print '''SMS
			From: %s
			To: %s
			Body:
			%s
			''' % (message_content['from_'], message_content['to'], message_content['body'])

	else:
		client.sms.messages.create(**message_content)
