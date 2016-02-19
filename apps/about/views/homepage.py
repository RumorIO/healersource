# coding=utf-8
import json
import random

from django.contrib.gis.geos.point import Point
from django.contrib.gis.measure import D
from django.db.models import Count
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.conf import settings
#from django.views.decorators.cache import cache_page

from util import utm_tracking
from about.utils import get_featured_providers, TOP_CITIES
from about.views import what_next
from account_hs.forms import (ClientSignupForm, HealerSignupForm, LoginFormHS,
							WellnessCenterSignupForm)
from healers.models import Healer, Zipcode
from healers.utils import is_healer
from healing_requests.models import HealingRequest, HealingRequestSearch
from healing_requests.forms import HealingRequestForm, HealingRequestSearchForm
from modality.models import get_modality_menu, Modality, ModalityCategory
from messages_hs.forms import ComposeFormUnregistered
from messages_hs.models import MessageExtra


def front_page(request):
	if request.user.is_authenticated():
		return what_next(request)
		#redirect('what_next')
	else:
		return homepage(request)
		#direct_to_template(request=request, template="about/front_page.html")


# @cache_page(60 * 60 * 24)
@utm_tracking
def homepage(request, template_name='about/homepage.html', **kwargs):
	if 'login' in request.POST:
		login_form = LoginFormHS(request.POST)
		if login_form.is_valid():
			login_form.login(request)
			return redirect(settings.LOGIN_REDIRECT_URLNAME)
	else:
		login_form = LoginFormHS()

	client_signup_form = ClientSignupForm()

	message = ""

	point = None
	zipcode = None

	quick_links = list(Zipcode.objects.filter(code__in=TOP_CITIES))
	quick_links.sort(key=lambda h: TOP_CITIES.index(h.code))

	for city_point in quick_links:
		city_healers = Healer.objects\
			.filter(clientlocation__location__point__distance_lte=(
				city_point.point, D(mi=50)))

		setattr(city_point, 'category', ModalityCategory.objects\
			.values('id', 'title')\
			.filter(modality__healer__in=city_healers)\
			.annotate(healers=Count('modality__healer'))\
			.order_by('-healers')[:10])

		setattr(city_point, 'modality', Modality.objects_approved\
			.values('id', 'title')\
			.filter(healer__in=city_healers)\
			.annotate(healers=Count('healer'))\
			.order_by('-healers')[:10])

	quick_links_category = ModalityCategory.objects\
		.values('id', 'title')\
		.annotate(healers=Count('modality__healer'))\
		.order_by('-healers')[:10]

	quick_links_modality = Modality.objects_approved\
		.values('id', 'title')\
		.annotate(healers=Count('healer'))\
		.order_by('-healers')[:10]

	if request.GET:
		lat = request.GET.get('lat', None)
		lon = request.GET.get('lon', None)
		if lat and lon:
			point = Point((float(lon), float(lat)))
			request.session['point'] = point
		else:
			request.session['point'] = None

	else:
		point = request.session.get('point', None)
		zipcode = request.session.get('zipcode', None)

	# will be needed if it's necessary to save selection of modality after searching from speciality page.
	# if 'modality_id' in session and 'modality2' not in session:
	# 	request.session['search_state']['modality'] = 'c:' + session['modality_id']

	featured_providers = get_featured_providers()
	random_username = random.choice(featured_providers)
	featured_providers.remove(random_username)
	featured_provider = None
	is_schedule_visible = False
	try:
		featured_provider = Healer.objects.get(user__username__iexact=random_username)
		is_schedule_visible = featured_provider.is_schedule_visible(request.user)
	except Healer.DoesNotExist:
		pass

	# for healing requests
	if request.user.is_authenticated():
		user = request.user
	else:
		user = None

	saved_searches = HealingRequestSearch.objects.filter(user=user, saved=True).order_by("-created_at")
	my_requests = HealingRequest.objects.filter(user=user).order_by('-created_at')

	context = {
		'login_form': login_form,
		'client_signup_form': client_signup_form,
		'compose_form': ComposeFormUnregistered(),
		'quick_links': quick_links,
		'quick_links_category': quick_links_category,
		'quick_links_modality': quick_links_modality,
		'message': message,
		'ip': request.META.get('HTTP_X_FORWARDED_FOR'),
		'point': point,
		'zipcode': zipcode,
		'modality_menu': get_modality_menu(),
		'featured_providers': json.dumps(featured_providers),
		'featured_provider': featured_provider,
		'is_schedule_visible': is_schedule_visible,
		# healing requests
		'is_healer': is_healer(request.user),
		'request_form': HealingRequestForm(),
		'recent_requests': HealingRequest.objects.all().order_by("-created_at"),
		'hr_search_form': HealingRequestSearchForm(),
		'saved_searches': HealingRequestSearch.objects.filter(user=user, saved=True).order_by("-created_at"),
		'my_requests': HealingRequest.objects.filter(user=user).order_by('-created_at'),
		'list_page': True,
		'SOURCE_CHOICE_HR': MessageExtra.SOURCE_CHOICE_HR,
		'hide_about': 'search' in request.GET or 'show_search' in request.GET or saved_searches or (my_requests and my_requests.exists()),
		'no_find_popup': True,
	}

	return render_to_response(
		template_name, context, context_instance=RequestContext(request, {}))
