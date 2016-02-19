from datetime import datetime, timedelta
from dateutil import rrule
from django import test
from django.core.urlresolvers import reverse
from django.core.management import call_command
from review.models import Review
from clients.models import Client
from healers.models import Clients, ClientInvitation,\
	Healer, TreatmentTypeLength, get_minutes
from healers.tests import create_appointment
from healers.templatetags.healer_tags import rating_star_css_class
from util import get_email, count_emails


def create_test_time():
	return datetime.utcnow().replace(hour=13, minute=0, second=0, microsecond=0)


class ReviewTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json', 'treatments.json']

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_client = Client.objects.get(pk=5)
		self.test_client.user.set_password('test')
		self.test_client.user.save()
		result_login = self.client.login(
			email=self.test_client.user.email,
			password='test')
		self.assertTrue(result_login)

		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.review_permission = Healer.VISIBLE_EVERYONE
		self.test_healer.save()
		self.username = self.test_healer.user.username

		self.friendship = Clients.objects.create(
			from_user=self.test_healer.user,
			to_user=self.test_client.user)


class ReviewFormTest(ReviewTest):

	def test_get_client_permission(self):
		self.test_healer.review_permission = Healer.VISIBLE_CLIENTS
		self.test_healer.save()
		self.friendship.delete()

		response = self.client.get(reverse('review_form', args=[self.username]))

		self.assertEqual(response.status_code, 404)

	def test_post_client_permission(self):
		self.test_healer.review_permission = Healer.VISIBLE_CLIENTS
		self.test_healer.save()
		self.friendship.delete()

		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test', 'review': 'Test', 'rating': 5})

		self.assertEqual(response.status_code, 404)

	def test_get_disable_permission(self):
		self.test_healer.review_permission = Healer.VISIBLE_DISABLED
		self.test_healer.save()

		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test', 'review': 'Test', 'rating': 5})

		self.assertEqual(response.status_code, 404)

	def test_add_get(self):
		response = self.client.get(reverse('review_form', args=[self.username]))

		self.assertEqual(response.status_code, 200)
		self.assertTrue('form' in response.context)
		self.assertEqual(response.context['form'].instance.pk, None)

	def test_add_post_title_length(self):
		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test', 'review': 'Test', 'rating': 5})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['form'].errors)

	def test_add_post_review_length(self):
		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test'*2, 'review': 'Test', 'rating': 5})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['form'].errors)

	def test_add_post(self):
		self.test_healer.ratings_1_star = 0
		self.test_healer.ratings_2_star = 0
		self.test_healer.ratings_3_star = 2
		self.test_healer.ratings_4_star = 2
		self.test_healer.ratings_5_star = 2
		self.test_healer.ratings_average = 4
		self.test_healer.save()

		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test'*2, 'review': 'Test'*5, 'rating': 5})

		self.assertEqual(response.status_code, 302)

		review = Review.objects.get(title='Test'*2, review='Test'*5)
		self.assertEqual(review.reviewer, self.test_client)
		self.assertEqual(review.healer, self.test_healer)
		self.assertEqual(review.rating, 5)

		self.test_healer = Healer.objects.get(pk=1)
		self.assertEqual(self.test_healer.ratings_5_star, 3)
		self.assertEqual(
			'%.2f' % self.test_healer.ratings_average,
			'%.2f' % (float(29)/7))

		self.assertEqual(count_emails(), 1)
		self.assertEqual(
			get_email().subject,
			'You have a new review on HealerSource!')

	def test_add_unapproved_client(self):
		"""
		#261 - review_permission is EVERYONE and a registered user writes
		a review for a healer, that client should be added to that healer's
		unapproved clients
		"""
		self.friendship.delete()
		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test'*2, 'review': 'Test'*5, 'rating': 5})

		self.assertEqual(response.status_code, 302)

		review = Review.objects.get(title='Test'*2, review='Test'*5)
		self.assertEqual(review.reviewer, self.test_client)
		self.assertEqual(review.healer, self.test_healer)
		self.assertEqual(review.rating, 5)

		unapproved_client = ClientInvitation.objects.filter(
			from_user=self.test_client.user,
			to_user=self.test_healer.user,
			status="2").count()
		self.assertEqual(unapproved_client, 1)

	def test_edit_get(self):
		review = Review.objects.create(
			healer=self.test_healer,
			reviewer=self.test_client,
			title='test',
			review='test',
			rating=4)
		response = self.client.get(reverse('review_form', args=[self.username]))

		self.assertEqual(response.status_code, 200)
		self.assertTrue('form' in response.context)
		self.assertEqual(response.context['form'].instance, review)

	def test_edit_post(self):
		review = Review.objects.create(
			healer=self.test_healer,
			reviewer=self.test_client,
			title='test',
			review='test',
			rating=4)

		self.test_healer.ratings_1_star = 0
		self.test_healer.ratings_2_star = 0
		self.test_healer.ratings_3_star = 2
		self.test_healer.ratings_4_star = 2
		self.test_healer.ratings_5_star = 2
		self.test_healer.ratings_average = 4
		self.test_healer.save()

		response = self.client.post(
			reverse('review_form', args=[self.username]),
			{'title': 'Test1'*2, 'review': 'Test1'*5, 'rating': 5})

		self.assertEqual(response.status_code, 302)

		review = Review.objects.get(pk=review.pk)
		self.assertEqual(review.reviewer, self.test_client)
		self.assertEqual(review.healer, self.test_healer)
		self.assertEqual(review.rating, 5)
		self.assertEqual(review.title, 'Test1'*2)

		self.test_healer = Healer.objects.get(pk=1)
		self.assertEqual(self.test_healer.ratings_4_star, 1)
		self.assertEqual(self.test_healer.ratings_5_star, 3)
		self.assertEqual(
			'%.2f' % self.test_healer.ratings_average,
			'%.2f' % (float(25)/6))

		self.assertEqual(count_emails(), 0)


class ReviewReminderCommandTestCase(ReviewTest):

	def setUp(self):
		super(ReviewReminderCommandTestCase, self).setUp()
		self.start = create_test_time() - timedelta(days=1)
		self.end = self.start + timedelta(hours=2)
		self.treatment_length = TreatmentTypeLength.objects.all()[0]

	def test_single(self):
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_review_reminders', *args, **opts)

		self.assertEqual(count_emails(), 1)

	def test_review_permission(self):
		self.test_healer.review_permission = Healer.VISIBLE_DISABLED
		self.test_healer.save()

		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_review_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)

	def test_repeat(self):
		self.start = create_test_time() - timedelta(days=4)
		self.end = self.start + timedelta(hours=2)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			repeat_period=rrule.DAILY,
			repeat_every=3,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_review_reminders', *args, **opts)

		self.assertEqual(count_emails(), 1)

	def test_no_yesterday_appts(self):
		self.start = create_test_time()
		self.end = self.start + timedelta(hours=2)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)

		self.start = create_test_time() - timedelta(days=2)
		self.end = self.start + timedelta(hours=2)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)

		self.start = create_test_time() - timedelta(days=3)
		self.end = self.start + timedelta(hours=2)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			repeat_period=rrule.DAILY,
			repeat_every=3,
			treatment_length=self.treatment_length)

		args = []
		opts = {}
		call_command('send_review_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)

	def test_review_exists(self):
		Review.objects.create(
			reviewer=self.test_client,
			healer=self.test_healer,
			title="Test",
			review="Test",
			rating=4)
		create_appointment(
			healer=self.test_healer,
			client=self.test_client,
			start_date=self.start.date(),
			end_date=self.end.date(),
			start_time=get_minutes(self.start),
			end_time=get_minutes(self.end),
			confirmed=True,
			treatment_length=self.treatment_length)
		args = []
		opts = {}
		call_command('send_review_reminders', *args, **opts)

		self.assertEqual(count_emails(), 0)


class RatingStarTest(test.TestCase):
	"""
	#258 - round overall rating to nearest 0.5 and
	use new stars for overall rating: icon_star_1 / icon_star_1_5
	"""

	def test_rating_4_0(self):
		self.assertEqual(rating_star_css_class(4.0), 'icon_star_4_0')

	def test_rating_4_1(self):
		self.assertEqual(rating_star_css_class(4.1), 'icon_star_4_0')

	def test_rating_4_3(self):
		self.assertEqual(rating_star_css_class(4.3), 'icon_star_4_5')

	def test_rating_4_5(self):
		self.assertEqual(rating_star_css_class(4.5), 'icon_star_4_5')

	def test_rating_4_6(self):
		self.assertEqual(rating_star_css_class(4.6), 'icon_star_4_5')

	def test_rating_4_8(self):
		self.assertEqual(rating_star_css_class(4.8), 'icon_star_5_0')
