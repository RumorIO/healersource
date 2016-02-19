from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from django.utils import timezone
from about.sitemap import SearchSitemap
from blog_hs.sitemap import BlogSitemap
from healers.sitemap import HealersSitemap
from modality.sitemap import ModalitySitemap


class VideosTourSitemap(Sitemap):
	priority = 0.8
	changefreq = 'weekly'
	lastmod = timezone.now()

	def location(self, obj):
		return reverse(obj)

	def items(self):
		return ['videos_list_all', 'tour']

healersource_sitemap = {
	'videos_tour': VideosTourSitemap,
	'healers': HealersSitemap,
	'specialties': ModalitySitemap,
	'blog': BlogSitemap,
	'searches': SearchSitemap
}
