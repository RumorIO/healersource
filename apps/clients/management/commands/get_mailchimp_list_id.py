from mailchimp import Mailchimp
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
	help = 'Outputs data for MAILCHIMP_LIST_ID'

	def handle(self, *args, **options):
		mailchimp = Mailchimp(settings.MAILCHIMP_KEY)
		return mailchimp.lists.list()['data'][0]['id']
