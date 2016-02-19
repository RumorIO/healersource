from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.text import slugify

search_top_cities = {
	'atlanta': '30301',
	'atlanta_ga': '30301',

	'boston': '02108',
	'boston_ma': '02108',

	'chicago': '60290',
	'chicago_il': '60290',

	'dallas': '75201',
	'dallas_tx': '75201',

	'houston': '77001',
	'houston_tx': '77001',

	'los_angeles': '90001',
	'los_angeles_ca': '90001',

	'new_york': '10001',
	'new_york_ny': '10001',

	'philadelphia': '19092',
	'philadelphia_pa': '19092',

	'phoenix': '85001',
	'phoenix_az': '85001',

	'san_francisco': '94102',
	'san_francisco_ca': '94102',

	'san_jose': '95106',
	'san_jose_ca': '95106',

	'washington': '20004',
	'washington_dc': '20004',

	'sedona': '86339',
	'sedona_az': '86339',

	'asheville': '28802',
	'asheville_nc': '28802',

	'ojai': '93024',
	'ojai_ca': '93024',

	'ashland': '97520',
	'ashland_or': '97520',

	'portland': '97202',
	'portland_or': '97202',

}
search_top_specialties = map(unicode ,[
	'Reiki', 'Energy Medicine', 'Deep Tissue Massage', 'Yoga',
	'Shamanic Healing', 'Life Coaching', 'Swedish Massage', 'Hatha Yoga',
	'Mindfulness Meditation', 'Tarot Card Readings', 'Pilates Exercise'
])
search_top_categories = map(unicode ,[
	'Energy Work', 'Massage', 'Spiritual Healing', 'Fitness & Movement',
	'Alternative Medicine', 'Counseling', 'Nutrition & Herbs',
	'Acupressure', 'Meditation Instruction', 'Acupuncture',
	'Breath Work', 'Yoga Instruction', 'Homeopathy', 'Beauty & Skin Care'
])


class SearchSitemap(Sitemap):
	priority = 0.8
	changefreq = 'weekly'
	lastmod = timezone.now()

	def location(self, obj):
		return reverse(obj['name'], kwargs=obj['args'])

	def items(self):
		urls = []
		for city in search_top_cities:
			urls.append({
				'name': 'search_seo_city',
				'args': {
					'city': city
				}
			})
			for speciality in search_top_specialties:
				urls.append({
					'name': 'search_seo_city_specialty',
					'args': {
						'city': city,
						'specialty': slugify(speciality)
					}
				})
			for category in search_top_categories:
				urls.append({
					'name': 'search_seo_city_specialty',
					'args': {
						'city': city,
						'specialty': slugify(category)
					}
				})
		return urls
