from urlparse import urlparse
from django.contrib.sitemaps import Sitemap
from healers.models import Healer


class HealersSitemap(Sitemap):
	priority = 0.8
	changefreq = 'weekly'

	def items(self):
		return Healer.objects.filter(user__avatar__isnull=False).exclude(profileVisibility=Healer.VISIBLE_CLIENTS)\
					.exclude(about='').order_by('-date_modified').distinct()

	def location(self, obj):
		url = urlparse(obj.get_full_url())
		return url.path

	def lastmod(self, obj):
		return obj.date_modified
