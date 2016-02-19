from random import shuffle
from django.contrib.auth.models import User
from clients.models import ClientLocation
from healers.models import Healer, Clients, Referrals, Zipcode
from healers.views import get_healers_geosearch


class RecommendationsFinder(object):
	def __init__(self, request, user_providers=None, recommendations_limit=5):
		self.recommendations_limit = recommendations_limit
		self.request = request
		self.user = request.user
		self.user_providers = user_providers
		self.recommendations = []
		self.execute()

	def execute(self):
		self.get_user_providers()
		# continue until found 5 providers or gone through all providers
		for provider in self.user_providers:
			if self.check_limit():
				# select random provider from my providers, return their
				# recommendations
				self.get_provider_recommendations(provider)

				# if that doesnt give 5 providers - do geosearch using
				# their default location zipcode
				# if that doesnt give 5 providers - try next location, etc.
				zipcode_list = ClientLocation.objects\
					.values_list('location__postal_code', flat=True)\
					.filter(client__user=provider)\
					.order_by('-location__is_default')
				zipcode_list = set(zipcode_list) # unique
				for zipcode in Zipcode.objects.filter(code__in=zipcode_list):
					if self.check_limit():
						self.do_geosearch(zipcode.point)
		if self.check_limit():
			self.add_random_providers()
		# final shuffle, because recommendations joined with geosearch
		shuffle(self.recommendations)

	def get_remaining_count(self):
		return self.recommendations_limit - len(self.recommendations)

	def check_limit(self):
		return self.get_remaining_count() > 0

	def get_user_providers(self):
		# implement in subclass
		pass

	def get_provider_recommendations(self, provider):
		recommendations = Referrals.objects.referrals_from(provider,
			exclude_users=self.get_exclude_users(),
			random=True,
			limit=self.recommendations_limit)
		recommendations = self.filter_by_visibility(
			f['friend'] for f in recommendations)
		self.recommendations.extend(recommendations)

	def add_random_providers(self):
		providers = self.visible_providers()\
						.exclude(user__in=self.recommendations)\
						.order_by('?')[:self.get_remaining_count()]
		self.recommendations.extend(p.user for p in providers)

	def filter_by_visibility(self, users):
		providers = self.visible_providers().filter(user__in=users)
		return (p.user for p in providers)

	def visible_providers(self):
		return Healer.objects\
					.filter(profileVisibility=Healer.VISIBLE_EVERYONE)\
					.exclude(user__in=User.objects.filter(avatar__isnull=True))\
					.exclude(about='')

	def do_geosearch(self, point):
		recommendations, more = get_healers_geosearch(self.request,
			point=point,
			exclude_users=self.get_exclude_users(),
			count=self.get_remaining_count(),
			random_order=True)
		self.recommendations.extend(provider.user for provider in recommendations)

	def get_exclude_users(self):
		return self.user_providers + [self.user] + self.recommendations


class ClientRecommendationsFinder(RecommendationsFinder):
	def get_user_providers(self):
		if not self.user_providers:
			self.user_providers = [
				f['friend'] for f in Clients.objects.referrals_to(self.user)]


class ProviderRecommendationsFinder(RecommendationsFinder):
	def execute(self):
		locations = self.get_user_locations()
		for location in locations:
			if self.check_limit():
				for zipcode in Zipcode.objects.filter(code=location):
					self.do_geosearch(zipcode.point)
		if self.check_limit():
			self.add_random_providers()

	def get_user_locations(self):
		return ClientLocation.objects\
			.values_list('location__postal_code', flat=True)\
			.filter(client__user=self.user, location__is_deleted=False)\
			.order_by('-location__is_default')

	def do_geosearch(self, point):
		recommendations, more = get_healers_geosearch(self.request,
			point=point,
			exclude_users=self.get_exclude_users(),
			random_order=True, distance=10)
		self.recommendations.extend(provider.user for provider in recommendations[:self.get_remaining_count()])


class ProviderRecommendationsFinderGeo(RecommendationsFinder):
	def execute(self):
		self.get_user_providers()
		for provider in self.user_providers:
			if self.check_limit():
				zipcode_list = ClientLocation.objects\
					.values_list('location__postal_code', flat=True)\
					.filter(client__user=provider)\
					.order_by('-location__is_default')
				zipcode_list = set(zipcode_list)

				for zipcode in Zipcode.objects.filter(code__in=zipcode_list):
					if self.check_limit():
						self.do_geosearch(zipcode.point)
		if self.check_limit():
			self.add_random_providers()

	def do_geosearch(self, point):
		recommendations, more = get_healers_geosearch(self.request,
			point=point,
			exclude_users=self.get_exclude_users(),
			count=self.get_remaining_count(),
			order_by_distance=True)
		self.recommendations.extend(
			provider.user for provider in recommendations)

	def get_user_providers(self):
		self.user_providers = [self.request.user,]
