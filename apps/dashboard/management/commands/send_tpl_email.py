from django.core.management.base import BaseCommand, CommandError
from dashboard.services.mail_sender import MailSender


class Command(BaseCommand):
	help = 'Send email from template'

	def handle(self, template=None, *args, **options):
		if args or template is None:
			raise CommandError('Usage is send_tpl_mail template_name')

		try:
			sender = MailSender(template)
		except Exception as e:
			raise CommandError(e)

		sender.send_emails()
