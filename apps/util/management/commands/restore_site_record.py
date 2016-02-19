from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):

	help = 'Restore Site Record'

	def handle(self, *args, **options):
		try:
			site = Site.objects.get()
		except Site.DoesNotExist:
			site = Site()
		site.name = 'Healersource'
		site.domain = 'www.healersource.com'
		site.save()
