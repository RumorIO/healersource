## -*- coding: utf-8 -*-
import csv
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from geonames.models import Country, GeoName


class Command(BaseCommand):

	help = 'Import countries from allCountries.txt'

	option_list = BaseCommand.option_list + (
		make_option(
			'--file',
			action='store',
			dest='file_path',
			help='path to allCountries.txt'),
	)

	def csv_reader(self, csvfile):
		csvfile.seek(0)
		reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
		for row in reader:
			yield [unicode(cell, 'utf-8') for cell in row]

	def handle(self, *args, **options):
		if not options['file_path']:
			raise CommandError(
				u'Provide --file option with path to allCountries.txt')

		self.stdout.write(u'Process file: {}'.format(options['file_path']))
		with open(options['file_path']) as csvfile:
			row_count = sum(1 for line in csvfile if not line.startswith('#'))
			self.stdout.write(u'Number of rows: {}'.format(row_count))

			reader = self.csv_reader(csvfile)
			row_index = 0
			count_skipped = 0
			count_created = 0
			for row in reader:
				if row[0].startswith('#'):
					continue

				row_index += 1
				try:
					try:
						population = int(row[14])
					except ValueError:
						population = 0
					if not population:
						count_skipped += 1
						self.stdout.write(u'{}/{}:\tskip 0 population'.format(
							row_index, row_count))
						continue

					try:
						country = Country.objects.get(code=row[8])
					except Country.DoesNotExist:
						self.stdout.write(u'{}/{}:\tERROR\tcan not find country {}'.format(
							row_index, row_count, row[8]))
						continue

					geoname = GeoName(
						name=unicode(row[1]),
						latitude=row[4],
						longitude=row[5],
						country=country,
						admin1=row[10],
						population=population
					)

					try:
						# save only with larger population
						exist_geoname = GeoName.objects.get(
							name=geoname.name,
							country=country,
							admin1=geoname.admin1)
						if exist_geoname.population >= geoname.population:
							count_skipped += 1
							self.stdout.write(u'{}/{}:\tskip exist'.format(
								row_index, row_count))
							continue
						else:
							count_created -= 1
							exist_geoname.delete()
					except GeoName.DoesNotExist:
						pass

					self.stdout.write(u'{}/{}:\t{}'.format(
						row_index, row_count, geoname))

					geoname.save()
					count_created += 1
				except Exception as e:
					self.stdout.write(u'{}/{}:\tERROR\t{}\t{}'.format(
						row_index, row_count, row, e))

			self.stdout.write(u'Skipped: {}/{}'.format(
				count_skipped, row_count))
			self.stdout.write(u'Created: {}/{}'.format(
				count_created, row_count))
