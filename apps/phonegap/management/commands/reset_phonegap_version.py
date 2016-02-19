from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):

	help = 'Reset phonegap version'

	def handle(self, *args, **options):
		app_version = int(args[0])
		if app_version == 1:
			path = settings.PHONEGAP_VERSION_FILE_PATH
		else:
			path = settings.PHONEGAP_VERSION2_FILE_PATH
		with open(path, 'w') as f:
			f.write('0')
