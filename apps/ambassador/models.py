# -*- coding: utf-8 -*-
from django.db import models


class Plan(models.Model):
	"""
	Ambassador plan - 9 month, 18 month, lifetime, etc..
	"""
	name = models.CharField(max_length=100)
	created_date = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return self.name


class Level(models.Model):
	"""
	Ambassador level - percent for each level, depends on plan
	"""
	plan = models.ForeignKey(Plan)
	level = models.PositiveSmallIntegerField(default=0)
	percent = models.FloatField(default=0)

	def __unicode__(self):
		return '{} Plan - Level {} - {}%'.format(
			self.plan, self.level+1, self.percent*100)

	class Meta:
		unique_together = ('plan', 'level')
		ordering = ['plan', 'level']
