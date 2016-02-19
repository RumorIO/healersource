# coding=utf-8
import csv
import cStringIO
import codecs
import os
import re
from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models.sql.aggregates import Count
from modality.models import Modality, ModalityCategory


TOP_CITIES = [
	#'30301',
	'02108',
	'60290',
	#'75201',
	'77001',
	'90001',
	'10001',
	'19092',
	'85001',
	'94102',
	'95106',
	#'20004',
	'86339',
	'28802',
	'93024',
	'97520',
	'97202']

"""
TOP_CATEGORIES = ModalityCategory.objects\
	.values('id', 'title')\
	.annotate(healers=Count('modality__healer'))\
	.filter(modality__healer__clientlocation__location__point__distance_lte=(
			point, D(mi=50)))\
	.order_by('-healers')[:10]


TOP_SPECIALTIES = specialties_top10 = Modality.objects_approved\
	.values('id', 'title')\
	.annotate(healers=Count('healer'))\
	.order_by('-healers')[:10]
"""


def get_featured_providers():
	"""Get providers usernames from images (png) in directory."""
	providers = []
	for f in os.listdir(settings.FEATURED_PROVIDERS_ROOT):
		m = re.search('^([\w\._-]+)\.png$', f)
		if m:
			providers.append(m.group(1))
	return providers


class UnicodeWriter:
	"""A CSV writer which will write rows to CSV file "f",
	which is encoded in the given encoding."""

	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		# Redirect output to a queue
		self.queue = cStringIO.StringIO()
		self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
		self.stream = f
		self.encoder = codecs.getincrementalencoder(encoding)()

	def writerow(self, row):
		self.writer.writerow([s.encode("utf-8") for s in row])
		# Fetch UTF-8 output from the queue ...
		data = self.queue.getvalue()
		data = data.decode("utf-8")
		# ... and reencode it into the target encoding
		data = self.encoder.encode(data)
		# write to the target stream
		self.stream.write(data)
		# empty queue
		self.queue.truncate(0)

	def writerows(self, rows):
		for row in rows:
			self.writerow(row)
