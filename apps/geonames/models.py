from django.db import models


class Country(models.Model):
	"""
	Country names from http://download.geonames.org/export/dump/countryInfo.txt
	"""
	code = models.CharField(max_length=2, primary_key=True)
	name = models.CharField(max_length=200)

	def __unicode__(self):
		return u'{}: {}'.format(self.code, self.name)


class GeoName(models.Model):
	"""
	Geo names from http://download.geonames.org/export/dump/allCountries.zip
	"""
	name = models.CharField(max_length=200)
	latitude = models.FloatField()
	longitude = models.FloatField()
	country = models.ForeignKey(Country)
	admin1 = models.CharField(max_length=20)
	population = models.PositiveIntegerField(db_index=True)

	def __unicode__(self):
		return u'{} ({}, {}) ({}, {})'.format(
			self.name, self.country, self.admin1,
			self.latitude, self.longitude)

	@property
	def short_name(self):
		if self.country.code == 'US':
			return u'{0.name}, {0.admin1}, {0.country.name}'.format(self)
		else:
			return u'{0.name}, {0.country.name}'.format(self)
