import csv
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from geonames.models import Country


class Command(BaseCommand):

	help = 'Import countries from countryInfo.txt'

	option_list = BaseCommand.option_list + (
		make_option(
			'--file',
			action='store',
			dest='file_path',
			help='path to countryInfo.txt'),
	)

	def handle(self, *args, **options):
		if not options['file_path']:
			raise CommandError(
				u'Provide --file option with path to countryInfo.txt')

		self.stdout.write(u'Process file: {}'.format(options['file_path']))
		with open(options['file_path']) as csvfile:
			reader = csv.reader(csvfile, delimiter='\t')
			row_count = sum(1 for row in reader if not row[0].startswith('#'))
			self.stdout.write(u'Number of rows: {}'.format(row_count))

			csvfile.seek(0)
			reader = csv.reader(csvfile, delimiter='\t')
			row_index = 0
			for row in reader:
				if row[0].startswith('#'):
					continue

				row_index += 1
				country = Country(code=row[0], name=row[4])

				self.stdout.write(u'{}/{}:\t{}'.format(
					row_index, row_count, country))

				country.save()
