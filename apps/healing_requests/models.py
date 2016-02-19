from django.db import models
from django.db.models.query_utils import Q
from django.contrib.gis.measure import D
from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.core.urlresolvers import reverse

from modality.models import ModalityCategory
from healers.models import Zipcode
from healers.utils import send_hs_mail
from util import (m2m_search_any, queryset_mix, full_url,
	starting_letters, SoftDeletionQuerySet)
from healing_requests.constants import *


def get_speciality_id(speciality):
	"""
	args: speciality (int)

	get_speciality_id(310)
	'p:2_c:310'
	"""

	def get_categories_options_specialty_ids():
		""" Return dict like {'c:310': 'p:2_c:310'} """
		output = {}
		from healing_requests import forms
		categories = forms.categories_as_choices()
		categories_choices = forms.get_specialities_choices()
		for x in range(0, len(categories)):
			category = categories[x][1]
			for n in range(1, len(category)):
				output[category[n][0]] = categories_choices[x][1][n][0]
		return output

	speciality_key = 'c:%d' % speciality
	try:
		return get_categories_options_specialty_ids()[speciality_key]
	except KeyError:
		return ':'


def process_specialities(specialities):
	"""Return list of specialties in 'c:n' format and remove duplicates.
	>>> process_specialities([u'p:8_c:148', u'p:8_c:108', u'p:4_c:108'])
	['c:148', 'c:108']
	"""
	specialities_output = set()
	for speciality in specialities:
		speciality = str(speciality)
		if '_' in speciality:
			specialities_output.add(speciality.split('_')[1])
		else:
			specialities_output.add(speciality)
	return list(specialities_output)


class HealingRequestAbstract(models.Model):
	location = models.ForeignKey('healers.Zipcode', null=True, blank=True)
	specialities = models.ManyToManyField('modality.Modality')
	speciality_categories = models.ManyToManyField('modality.ModalityCategory')
	remote_healing = models.BooleanField(default=False)
	trade_for_services = models.BooleanField(default=False)
	cost_per_session = models.PositiveSmallIntegerField(null=True, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	objects = geomodels.GeoManager()

	class Meta:
		abstract = True


def get_speciality_ids(search_specialities):
	search_specialities = process_specialities(search_specialities)
	specs = set()
	for spec in search_specialities:
		type, id = spec.split(':')
		id = int(id)
		if type == 'c':
			specs.add(id)
		else:
			specs |= set(ModalityCategory.objects.get(pk=id).modality_set.all().values_list('pk', flat=True))
	return list(specs)


class HealingRequestSearch(HealingRequestAbstract):
	user = models.ForeignKey('auth.User', null=True, blank=True)
	near_my_location = models.BooleanField(default=False)
	only_my_specialities = models.BooleanField(default=False)
	saved = models.BooleanField(default=False)

	class Meta:
		abstract = False

	@classmethod
	def search(cls, params):
		queryset = HealingRequestSearch.objects.filter(saved=True).order_by("-created_at")

		specialities = []

		if params.get('specialities', None):
			specialities = get_speciality_ids(params.get('specialities'))

		if params.get('specialities_ids', None):
			specialities = params.get('specialities_ids')

		if specialities:
			q1 = queryset.filter(only_my_specialities=False)
			q1_ = m2m_search_any(HealingRequestSearch, 'specialities', specialities, q1)
			q1_c = HealingRequestSearch.objects.none()
			if params.get("speciality_categories", None):
				q1_c = m2m_search_any(HealingRequestSearch, 'speciality_categories',
					params.get("speciality_categories"), q1)

			q1 = q1_ | q1_c

			q2 = queryset.filter(only_my_specialities=True)
			q2 = m2m_search_any(HealingRequestSearch, 'user__client__healer__modality', specialities, q2)

			queryset = q1 | q2
		else:
			if params.get("speciality_categories", None):
				queryset = m2m_search_any(HealingRequestSearch, 'speciality_categories',
					params.get("speciality_categories"), queryset)

		if params.get('location', None):
			q1 = queryset.filter(
				near_my_location=False,
				location__point__distance_lte=(params['location'].point, D(mi=50)))

			q2 = queryset.filter(
				near_my_location=True,
				user__client__healer__clientlocation__location__point__distance_lte=(
					params['location'].point, D(mi=50)))

			q3 = None
			if params.get("remote_healing", None) is not None:
				q3 = queryset.filter(remote_healing=params['remote_healing'])

			if q3 is not None:
				queryset = q1 | q2 | q3
			else:
				queryset = q1 | q2

		q4, q5 = None, None
		if params.get("trade_for_services", None) is not None:
			q4 = queryset.filter(trade_for_services=params['trade_for_services'])

		if params.get("cost_per_session", None):
			q5 = queryset.filter(cost_per_session__lte=params.get('cost_per_session'))

		queryset = queryset_mix(q4, q5, queryset)

		queryset = queryset.distinct()

		return queryset

	def get_search_param_string(self):
		"""
			Adds extra param 'show_search' to denote this is old search (wont be saved again, until you submit)
			Adds extra param search_id
		"""
		params = {
			'show_search': True,
			'search_id': self.id
		}
		if self.near_my_location:
			params['near_my_location'] = True
		elif self.location:
			params['zipcode'] = self.location.id
			params['near_my_location'] = False
			params['search_city_or_zipcode'] = "%s, %s" % (
				self.location.city, self.location.state)

		params['cost_per_session'] = self.cost_per_session
		if params['cost_per_session']:
			params['accept_cost_per_session'] = True

		params['remote_healing'] = self.remote_healing
		params['trade_for_services'] = self.trade_for_services
		params['saved'] = self.saved

		specialities = []
		speciality_categories = []
		if self.only_my_specialities:
			params['only_my_specialities'] = True
		else:
			specialities = self.specialities.all().values_list('id', flat=True)
			if len(specialities) > 0:
				params['only_my_specialities'] = False
			speciality_categories = self.speciality_categories.all().values_list('id', flat=True)
			if len(speciality_categories) > 0:
				params['only_my_specialities'] = False

		string = ""
		for key in params:
			string += "%s=%s&" % (key, params[key])

		speciality_str = ""
		for speciality in specialities:
			speciality_str += "search_specialities=%s&" % get_speciality_id(speciality)

		string += speciality_str

		speciality_categories_str = ""
		for cat in speciality_categories:
			speciality_categories_str += "search_specialities=p:%d&" % cat

		string += speciality_categories_str

		string = string.rstrip("&")
		return string


class HealingRequestManager(geomodels.GeoManager):

	def __init__(self, *args, **kwargs):
		self.all_objects = kwargs.pop('all_objects', False)
		super(HealingRequestManager, self).__init__(*args, **kwargs)

	def get_queryset(self):
		if self.all_objects:
			return SoftDeletionQuerySet(self.model)
		else:
			return SoftDeletionQuerySet(self.model).alive()


class HealingRequest(HealingRequestAbstract):

	user = models.ForeignKey('auth.User', related_name='healing_requests')
	title = models.CharField(max_length=255)
	description = models.TextField()
	show_full_name = models.BooleanField(default=False)
	show_photo = models.BooleanField(default=False)
	status = models.PositiveSmallIntegerField(choices=HR_STATUSES,
		null=True, blank=True)

	objects = HealingRequestManager()
	all_objects = HealingRequestManager(all_objects=True)

	class Meta:
		abstract = False

	def __unicode__(self):
		return u"%s" % self.title

	def delete(self):
		self.status = HR_STATUS_DELETE
		self.save()

	def hard_delete(self):
		super(HealingRequest, self).delete()

	def absolute_url(self):
		return full_url(reverse("show_healing_request", args=[self.id]))

	def user_display_name(self):
		if self.show_full_name:
			return self.user.first_name
		else:
			return starting_letters(self.user.get_full_name())

	def add_specialities(self, specialities):
		current_ids = self.specialities.all().values_list('id', flat=True)
		specialities = map(int, specialities)
		for speciality_id in specialities:
			if speciality_id not in current_ids:
				self.specialities.add(speciality_id)

	def mail_matched_searches(self):
		params = {
			'remote_healing': self.remote_healing,
			'trade_for_services': self.trade_for_services,
			'cost_per_session': self.cost_per_session,
			'specialities_ids': self.specialities.all().values_list('id', flat=True),
			'speciality_categories': self.speciality_categories.all().values_list('id', flat=True),
			'location': self.location,
		}
		queryset = HealingRequestSearch.search(params)
		subject = 'New Healing Request matching your saved search'
		for obj in queryset:
			search_link = full_url(reverse('show_healing_request_search', args=[obj.id]))
			request_link = full_url(reverse('show_healing_request', args=[self.id]))
			context = {
				'search_link': search_link,
				'title': self.title,
				'description': self.description,
				'request_link': request_link
			}
			send_hs_mail(subject, 'healing_requests/emails/new_matched_request.txt',
				context, settings.DEFAULT_FROM_EMAIL, [obj.user.email])

	@classmethod
	def search(cls, params):
		queryset = HealingRequest.objects.filter(user__is_active=True).order_by("-created_at")
		q_location = None

		if params.get("near_my_location", None) and params.get("is_healer", None):
			locations = params["is_healer"].clientlocation_set.all()
			q = None
			filters = [Q(location__point__distance_lte=(location.location.point, D(mi=50))) for location in locations if location.location.point]
			for f in filters:
				q = q | f if q else f
			if len(filters):
				q_location = queryset.filter(q)

		elif params.get("near_my_location", None) is False and params.get("zipcode", None):

			zipcode = Zipcode.objects.get(id=params['zipcode'])
			q_location = queryset.filter(location__point__distance_lte=(zipcode.point, D(mi=50)))

		if params.get("remote_healing", None):
			q_remote = queryset.filter(remote_healing=params['remote_healing'])
			if q_location is not None:
				queryset = queryset_mix(q_location, q_remote, queryset)
			else:
				queryset = q_remote
		elif q_location is not None:
			queryset = q_location

		q5, q6 = None, None

		if params.get("cost_per_session", None) and params.get("accept_cost_per_session", None):
			q5 = queryset.filter(cost_per_session__gte=params["cost_per_session"])

		if params.get("trade_for_services", None):
			q6 = queryset.filter(trade_for_services=params['trade_for_services'])

		queryset = queryset_mix(q5, q6, queryset)

		specialities = speciality_categories = []

		def get_speciality_categories_ids(search_specialities):
			cats = []
			for cat in search_specialities:
				if cat.startswith('p:') and '_' not in cat:
					id = cat.split(':')[1]
					cats.append(id)
			return cats

		if params.get("only_my_specialities", None):
			if params.get("is_healer", None):
				specialities = params["is_healer"].modality_set.values_list("id", flat=True)

		elif params.get("search_specialities", None):
			specialities = get_speciality_ids(params['search_specialities'])
			speciality_categories = get_speciality_categories_ids(params['search_specialities'])

		if specialities:
			q = m2m_search_any(HealingRequest, 'specialities', specialities, queryset)
			q_c = HealingRequestSearch.objects.none()
			if speciality_categories:
				q_c = m2m_search_any(HealingRequest, 'speciality_categories', speciality_categories, queryset)

			queryset = q | q_c

		elif speciality_categories:
			queryset = m2m_search_any(HealingRequest, 'speciality_categories', speciality_categories, queryset)

		return queryset
