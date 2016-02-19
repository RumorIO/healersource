from urlparse import urlparse
from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from mezzanine.blog.models import BlogPost
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED


class BlogSitemap(Sitemap):
	priority = 0.8
	changefreq = 'weekly'

	def items(self):
		return BlogPost.objects.filter(status=CONTENT_STATUS_PUBLISHED, user__avatar__isnull=False)\
			.select_related('user').order_by("-publish_date").distinct()

	def location(self, obj):
		return reverse('blog_post', kwargs={'username': obj.user.username,
											'year': obj.publish_date.year,
											'month': obj.publish_date.strftime("%m"),
											'slug_id': obj.pk})

	def lastmod(self, obj):
		return obj.publish_date
