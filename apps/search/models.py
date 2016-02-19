from django.db import models
from django.contrib.auth.models import User

from modality.models import Modality, ModalityCategory
from healers.models import Zipcode

class HealerSearchHistory(models.Model):
	user = models.ForeignKey(User, null=True, blank=True)
	zipcode = models.ForeignKey(Zipcode, null=True, blank=True)
	modality = models.ForeignKey(Modality, null=True, blank=True)
	modality_category = models.ForeignKey(ModalityCategory, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		if self.zipcode:
			temp = self.zipcode.city
		elif self.modality:
			temp = self.modality
		elif self.modality_category:
			temp = self.modality_category
		else:
			temp = ''
		return u'%s' % temp