from django import test
from django.core.urlresolvers import reverse

from oauth_access.models import UserAssociation
from clients.models import Client
from healers.models import WellnessCenter
from ambassador.models import Plan, Level
from ambassador.settings import COOKIE_NAME


class AmbassadorTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		self.ambassador = Client.objects.get(pk=5)
		self.ambassador.ambassador_program = True
		self.ambassador.save()
		self.ambassador.user.set_password('test')
		self.ambassador.user.save()

		self.client.login(
			email=self.ambassador.user.email,
			password='test')

		self.create_plans()

	def set_stripe(self, connect=True):
		if connect:
			UserAssociation.objects.get_or_create(
				user=self.ambassador.user, service='stripe')
		else:
			UserAssociation.objects.filter(
				user=self.ambassador.user, service='stripe').delete()

	def set_plan(self, plan):
		self.ambassador.ambassador_plan = plan
		self.ambassador.save()

	def create_plans(self):
		self.plans = []
		# 9-month plan
		plan = Plan.objects.create(name='9-month')
		Level.objects.create(plan=plan, level=0, percent=0.5)
		Level.objects.create(plan=plan, level=1, percent=0.2)
		Level.objects.create(plan=plan, level=2, percent=0.1)
		self.plans.append(plan)

		# 18-month plan
		plan = Plan.objects.create(name='18-month')
		Level.objects.create(plan=plan, level=0, percent=0.25)
		Level.objects.create(plan=plan, level=1, percent=0.15)
		Level.objects.create(plan=plan, level=2, percent=0.05)
		self.plans.append(plan)

		# Lifetime plan
		plan = Plan.objects.create(name='Lifetime')
		Level.objects.create(plan=plan, level=0, percent=0.15)
		Level.objects.create(plan=plan, level=1, percent=0.05)
		Level.objects.create(plan=plan, level=2, percent=0.02)
		self.plans.append(plan)


class AmbassadorRedirectViewTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		self.ambassador = Client.objects.get(pk=5)
		self.ambassador.ambassador_program = True
		self.ambassador.save()

	def test_urls(self):
		urls = ['front_page', 'tour', 'signup', 'signup_plugin',
				'landing_page_notes']
		for url in urls:
			response = self.client.get(
				reverse(
					'ambassador:' + url,
					args=[self.ambassador.user.username]),
				follow=True)

			self.assertRedirects(response, reverse(url), 302)
			self.assertEqual(
				response.client.cookies[COOKIE_NAME].value,
				self.ambassador.user.username)


class DashboardViewTest(AmbassadorTest):

	def test_no_plan(self):
		self.set_stripe()
		response = self.client.get(
			reverse('ambassador:dashboard'), follow=True)

		self.assertRedirects(response, reverse('ambassador:settings'), 302)

	def test_no_stripe(self):
		response = self.client.get(
			reverse('ambassador:dashboard'), follow=True)

		self.assertRedirects(response, reverse('ambassador:promo'), 302)

	def test_success(self):
		self.set_stripe()
		self.set_plan(self.plans[0])
		response = self.client.get(
			reverse('ambassador:dashboard'), follow=True)

		self.assertEqual(response.status_code, 200)


class SettingsViewTest(AmbassadorTest):

	def test_no_stripe(self):
		response = self.client.get(
			reverse('ambassador:settings'), follow=True)

		self.assertRedirects(response, reverse('ambassador:promo'), 302)

	def test_get(self):
		self.set_stripe()
		response = self.client.get(
			reverse('ambassador:settings'), follow=True)

		self.assertEqual(response.status_code, 200)
		self.assertTrue('forms' in response.context)

	def test_post_ambassador(self):
		self.set_stripe()
		data = {'plan': self.plans[1].pk, 'form_name': 'ambassador'}
		response = self.client.post(
			reverse('ambassador:settings'), data)

		self.assertRedirects(response, reverse('ambassador:dashboard'), 302)

		c = Client.objects.get(pk=self.ambassador.pk)
		self.assertEqual(c.ambassador_plan, self.plans[1])

	def test_post_embed_background_color(self):
		self.set_stripe()
		self.set_plan(self.plans[1])
		data = {'background_color': 'aabbcc', 'form_name': 'embed'}
		response = self.client.post(
			reverse('ambassador:settings'), data, follow=True)

		self.assertRedirects(response, reverse('ambassador:dashboard'), 302)

		c = Client.objects.get(pk=self.ambassador.pk)
		self.assertEqual(c.embed_background_color, '#aabbcc')

	def test_post_embed_background_color_empty(self):
		self.set_stripe()
		self.set_plan(self.plans[1])

		data = {'background_color': '', 'form_name': 'embed'}
		c = Client.objects.get(pk=self.ambassador.pk)

		response = self.client.post(
			reverse('ambassador:settings'), data, follow=True)

		self.assertRedirects(response, reverse('ambassador:dashboard'), 302)

		c = Client.objects.get(pk=self.ambassador.pk)
		self.assertEqual(c.embed_background_color, '')

	def test_post_embed_search_all_false(self):
		wc = WellnessCenter.objects.create(
			client_ptr=self.ambassador,
			user=self.ambassador.user)
		wc.embed_search_all = True
		wc.save()

		self.set_stripe()
		self.set_plan(self.plans[1])

		data = {
			'search_all': '0',
			'background_color': '#aabbcc',
			'form_name': 'embed'}
		response = self.client.post(
			reverse('ambassador:settings'), data)

		self.assertRedirects(response, reverse('ambassador:dashboard'), 302)

		c = Client.objects.get(pk=self.ambassador.pk)
		self.assertEqual(c.embed_background_color, '#aabbcc')
		self.assertEqual(c.embed_search_all, False)

	def test_post_embed_search_all_true(self):
		wc = WellnessCenter.objects.create(
			client_ptr=self.ambassador,
			user=self.ambassador.user)
		wc.embed_search_all = False
		wc.save()

		self.set_stripe()
		self.set_plan(self.plans[1])

		data = {
			'search_all': '1',
			'background_color': '#aabbcc',
			'form_name': 'embed'}
		response = self.client.post(
			reverse('ambassador:settings'), data)

		self.assertRedirects(response, reverse('ambassador:dashboard'), 302)

		c = Client.objects.get(pk=self.ambassador.pk)
		self.assertEqual(c.embed_background_color, '#aabbcc')
		self.assertEqual(c.embed_search_all, True)


class AmbassadorHomePageTest(AmbassadorTest):

	def test_what_next_redirect(self):
		self.ambassador.ambassador_program = True
		self.ambassador.save()
		response = self.client.get(
			reverse('what_next'), follow=True)

		self.assertRedirects(response, reverse('ambassador:promo'), 302)


class AmbassadorPluginViewTest(AmbassadorTest):

	def setUp(self):
		super(AmbassadorPluginViewTest, self).setUp()
		self.client.logout()

		self.url = reverse(
			'ambassador:plugin',
			args=[self.ambassador.user.username])

	def test_get(self):
		response = self.client.get(self.url, follow=True)

		self.assertEqual(response.status_code, 200)

		self.assertEqual(
			response.client.cookies[COOKIE_NAME].value,
			self.ambassador.user.username)
