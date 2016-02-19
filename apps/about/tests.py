from django import test
from django.core.urlresolvers import reverse
from about.urls import urlpatterns

"""
class AboutTest(test.TestCase):
	def test_responses(self):
		for url in urlpatterns:
			print(url)
			response = self.client.get(reverse(url.name))
			if url.name == "what_next":
				self.assertEqual(response.status_code, 302)
			else:
				self.assertEqual(response.status_code, 200)
"""
