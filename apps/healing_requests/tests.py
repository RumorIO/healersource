from django import test
from django.core.urlresolvers import reverse
from healing_requests.models import HealingRequest
from healers.models import Healer
from avatar.models import Avatar
from django_dynamic_fixture import G
from captcha.models import CaptchaStore
from captcha import conf


class HealingRequestsBaseTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'locations.json',
	'healing_requests.json', 'zipcodes.json', 'healing_requests_modalities.json']

	def setUp(self):
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()
		G(Avatar, user=self.test_healer.user)
		G(Avatar, user=Healer.objects.get(pk=3).user)
		self.search_request = {
			'search': True,
		}

	def search(self):
		response = self.client.get(reverse('healing_request_home'), self.search_request, follow=True)
		results = response.context['search_results']
		if results:
			return results.values_list('pk', flat=True)


class HealingRequestsTestAnonymous(HealingRequestsBaseTest):
	def test_healing_requests_not_visible_if_user_is_not_active(self):
		challenge, response = conf.settings.get_challenge()()
		store = CaptchaStore.objects.create(challenge=challenge, response=response)

		response = self.client.post(reverse('healing_request_home'), {
			'first_name': 'First',
			'last_name': 'last',
			'email': 'test@test.com',
			'password1': '11111111',
			'password2': '11111111',
			'security_verification_0': store.hashkey,
			'security_verification_1': store.response,
			'title': 'test_request',
			'description': 'test',
		}, follow=True)
		self.assertEqual(response.status_code, 200)

		# make sure that healing request has been created

		# originally - 5 +1 new
		self.assertEqual(HealingRequest.objects.all().count(), 6)

		self.client.login(email=self.test_healer.user.email, password='test')

		# search for all requests
		ids = self.search()

		self.assertEqual(len(ids), 5)


class HealingRequestsTestAuthenticated(HealingRequestsBaseTest):
	def setUp(self):
		super(HealingRequestsTestAuthenticated, self).setUp()
		self.client.login(email=self.test_healer.user.email, password='test')

	def assertEqualSet(self, a, b):
		return self.assertEqual(set(a), set(b))

	def test_remote_healing(self):
		self.search_request['remote_healing'] = True
		ids = self.search()
		self.assertEqualSet(ids, [1, 2])

	def test_trade_for_services(self):
		self.search_request['trade_for_services'] = True
		ids = self.search()
		self.assertEqualSet(ids, [2, 3])

	def test_location_near_city(self):
		self.search_request['zipcode'] = 4
		ids = self.search()
		self.assertEqualSet(ids, [1, 4])

	def test_location_anywhere(self):
		self.search_request['zipcode'] = 0
		self.search_request['search_city_or_zipcode'] = 'Everywhere'
		ids = self.search()
		self.assertEqual(len(ids), HealingRequest.objects.count())

	def test_location_near_my_location(self):
		# City - Brooklyn / New York
		self.search_request['near_my_location'] = True
		ids = self.search()
		self.assertEqualSet(ids, [2])

	def test_min_cost_per_session(self):
		self.search_request['cost_per_session'] = 100
		self.search_request['accept_cost_per_session'] = True
		ids = self.search()
		self.assertEqualSet(ids, [2, 3])

	def test_only_my_specialities(self):
		self.search_request['only_my_specialities'] = True
		ids = self.search()
		self.assertEqualSet(ids, [1, 2, 3, 4])

	def test_specific_specialities(self):
		self.search_request['search_specialities'] = 'p:2_c:2'
		self.search_request['only_my_specialities'] = False
		ids = self.search()
		self.assertEqualSet(ids, [2, 3, 4])

		self.search_request['search_specialities'] = 'p:2_c:3'
		ids = self.search()
		self.assertEqualSet(ids, [4])

	def test_any_speciality(self):
		HealingRequest.objects.create(user=self.test_healer.user,
			title='test', description='description')
		ids = self.search()
		self.assertEqual(len(ids), 6)

	def test_specific_specialities_multiple(self):
		self.search_request['search_specialities'] = ['p:1_c:1', 'p:2_c:3']
		self.search_request['only_my_specialities'] = False
		ids = self.search()
		self.assertEqualSet(ids, [1, 3, 4])

	def test_specific_specialities_category(self):
		self.search_request['search_specialities'] = 'p:2'
		self.search_request['only_my_specialities'] = False
		ids = self.search()
		self.assertEqualSet(ids, [2, 3, 4, 5])

	# Request delete tests
	def test_delete_other(self):
		response = self.client.post(reverse('delete_healing_request', args=[5]))
		self.assertEqual(response.status_code, 404)

	def test_delete_own(self):
		response = self.client.post(reverse('delete_healing_request', args=[1]))
		self.assertEqual(response.status_code, 302)
		self.assertFalse(HealingRequest.objects.filter(pk=1).exists())
