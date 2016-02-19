from urlparse import urlparse
from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from modality.models import Modality


class ModalitySitemap(Sitemap):
	priority = 0.8
	changefreq = 'weekly'

	def items(self):
		return Modality.objects_approved.all().distinct()

	def location(self, obj):
		return reverse('modality_description_full_page', kwargs={'modality_id': obj.pk})
