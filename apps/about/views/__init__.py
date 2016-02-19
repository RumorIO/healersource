# coding=utf-8

import os
import json
import operator
import random
from datetime import timedelta
from collections import defaultdict

from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.measure import D
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest, QueryDict
from django.utils.timezone import datetime
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from django_messages.models import Message
from mezzanine.blog.models import BlogPost
from oauth_access.models import UserAssociation
from rest_framework.response import Response
from rest_framework.views import APIView

from util import add_to_mailchimp, utm_tracking, full_url
from healing_requests.models import HealingRequest, HealingRequestSearch
from modality.models import get_modality_menu, Modality, ModalityCategory
from messages_hs.forms import ComposeFormUnregistered
from search.utils import add_to_healer_search_history
from intake_forms.models import IntakeFormSentHistory, IntakeForm
from messages_hs.models import UnregisteredMessage, MessageExtra
from account_hs.authentication import user_authenticated, user_is_superuser
from account_hs.forms import ClientSignupForm
from clients.models import Client, SiteJoinInvitation, ReferralsSent, ClientVideo
from client_notes.models import Note
from phonegap.utils import render_page
from healers.forms import HealerSearchForm, ConciergeForm
from healers.models import (Healer, Referrals, Appointment, Zipcode,
	WellnessCenter, is_healer, get_account_type, Concierge, Clients)
from healers.utils import (Setup_Step_Names, get_fill_warning_links,
							send_hs_mail, get_full_url)
from healers.views import get_healers_geosearch
from payments.models import Payment, Customer, Charge
from send_healing.utils import ghp_members
from send_healing.models import SentHealing

from about.utils import TOP_CITIES, UnicodeWriter, get_featured_providers
from about.models import UserAssociationDated
from about.sitemap import (search_top_categories, search_top_cities,
	search_top_specialties)


@login_required
def what_next(request):
	def get_suggested_recommendations():
		from friends_app.recommendations import ProviderRecommendationsFinder
		referrals_from_me = [o["friend"] for o in Referrals.objects.referrals_from(request.user)]
		return ProviderRecommendationsFinder(request, referrals_from_me, recommendations_limit=4).recommendations

	client = get_object_or_404(Client, user=request.user)
	healer = is_healer(request.user)
	first_login_cached = client.first_login
	if first_login_cached:
		client.first_login = False
		client.save()
		if healer:
			return redirect('provider_setup', 0)
		else:
			incomplete_forms = client.incomplete_forms()
			if incomplete_forms:
				return redirect('intake_form_answer',
					incomplete_forms[0].healer.user.username)

	if not healer:
		if request.user.client.ambassador_program:
			return redirect('ambassador:dashboard')
		return redirect('friends', 'healers')

	fill_warning_links = get_fill_warning_links(healer)
	# referrals_to_me_count = Referrals.objects.referrals_to(healer.user, count=True)

	request.step_names = Setup_Step_Names.get_steps(healer)

	suggested_recommendations = get_suggested_recommendations()

	return render_to_response('about/what_next.html', {
		'healer': healer,
		'fill_warning_links': fill_warning_links,
		# 'referrals_to_me_count': referrals_to_me_count,
		"suggested_recommendations": suggested_recommendations,
		'friend_type': 'referrals',
		"first_login": first_login_cached,
		'editing_self': True,
	}, context_instance=RequestContext(request))


@user_is_superuser
def wcenter(request):
	wellness_centers = WellnessCenter.objects.all().order_by('-pk')

	output = []
	for wellness_center in wellness_centers:
		referrals_to_me_count = Referrals.objects.referrals_from(wellness_center.user, count=True)
		output.append({
			'title': wellness_center.user.username,
			'url': wellness_center.get_full_url,
			'date': wellness_center.user.date_joined,
			'providers': referrals_to_me_count,
		})

	return render_to_response('about/wellness_center_list.html', {
		'wellness_centers': output,
	}, context_instance=RequestContext(request))


def get_city_select_code(query):
	if 'city' in query and 'state' in query:
		if query['city'] and query['state']:
			zipcodes = Zipcode.objects\
				.filter(city=query['city'].upper(), state=query['state'])\
				.values_list('id')
			if zipcodes:
				return max(zipcodes)[0]
	return 0

DAY_VALUES = [1, 2, 3, 7, 14, 30, 60, 90, 180, 365]


def render_search(extra_context, request=None, template=None):
	if template is None:
		template = 'about/search_results.html'

	ctx = {
		'search_form': HealerSearchForm(),
		'compose_form': ComposeFormUnregistered(),
		'modality_menu': get_modality_menu(),
		'no_find_popup': True,
		'url_search': '%s%s' % (settings.DEFAULT_HTTP_PROTOCOL, full_url(reverse('search_ajax'))),
	}

	return render_page(request, template, ctx, extra_context)


def search(request, template_name=None, modality=None,
			city=None, specialty=None, all=False, skip_first_hr=False,
			state=None, embed_user=None, phonegap=False):

	"""
	Search providers by parameters of HealerSearchForm
	skip_first_hr - false to show hr in infinite scroll
	"""

	def get_concierge_and_city():
		if not point:
			return None, None

		concierges = Concierge.objects.all().values_list('pk', flat=True)
		healers = Healer.objects.filter(
			clientlocation__location__point__distance_lte=(point, D(mi=50)), pk__in=concierges).distinct()
		if healers:
			healer = healers[0]
			return healers[0], healer.clientlocation_set.filter(location__point__distance_lte=(point, D(mi=50)))[0].location.city
		return None, None

	def get_stats():
		def filter_last_30_days(qset, field_name, date_field_name):
			fiter_name = '%s__%s__gte' % (field_name, date_field_name)
			filters = {fiter_name: datetime.today() - timedelta(30)}
			return qset.filter(**filters)

		def get_specialties_top10():
			specialties_top10 = (Modality.objects_approved
				.values('title')
				.annotate(healers=Count('healer'))
				.order_by('-healers'))
			specialties_top10_complete = (Modality.objects_approved
				.filter(healer__in=healers_complete)
				.values('title')
				.annotate(healers_c=Count('healer'))
				.order_by('-healers_c'))
			specialties_top10 = specialties_top10[:10]
			specialties_top10_complete = specialties_top10_complete[:10]
			return healers_complete_combiner(
				specialties_top10, specialties_top10_complete)

		def get_specialties_categories():
			specialties_categories = (ModalityCategory.objects
				.values('title')
				.annotate(healers=Count('modality__healer'))
				.order_by('-healers'))
			specialties_categories_complete = (ModalityCategory.objects
				.filter(modality__healer__in=healers_complete)
				.values('title')
				.annotate(healers_c=Count('modality__healer'))
				.order_by('-healers_c'))
			return healers_complete_combiner(
				specialties_categories, specialties_categories_complete)

		def get_healers_in_zip():
			zip_city = (Zipcode.objects
				.filter(code__in=TOP_CITIES)
				.values('code', 'city', 'state', 'point'))

			healers_in_zip = {}
			healers_in_zip_complete = {}

			for zipcode in zip_city:
				hz = Healer.objects.filter(
					clientlocation__location__point__distance_lte=
					(zipcode['point'], D(mi=50))).distinct()
				healers_in_zip.update({zipcode['code']: hz.count()})
				hz = Healer.objects.filter(
					clientlocation__location__point__distance_lte=
					(zipcode['point'], D(mi=50)),
					pk__in=healers_complete).distinct()
				healers_in_zip_complete.update({zipcode['code']: hz.count()})

			healers_in_zip = [{
				'code': z['code'],
				'city': z['city'],
				'state': z['state'],
				'healers': healers_in_zip.get(z['code'], 0),
				'healers_c': healers_in_zip_complete.get(z['code'], 0)
				} for z in zip_city]

			healers_in_zip.sort(key=lambda h: TOP_CITIES.index(h['code']))
			return healers_in_zip

		def get_intake_form():
			now = datetime.now().date()
			intake_form_stats = {'created': [], 'sent': []}
			intake_forms = IntakeForm.objects.all()
			intake_forms_sent = IntakeFormSentHistory.objects.all()
			for n in DAY_VALUES:
				start_day = now - timedelta(n)
				intake_form_stats['created'].append(intake_forms.filter(
					created_at__range=(start_day, now)).count())
				intake_form_stats['sent'].append(intake_forms_sent.filter(
					created_at__range=(start_day, now)).count())
			intake_form_stats['created'].append(intake_forms.count())
			intake_form_stats['sent'].append(intake_forms_sent.count())
			return intake_form_stats

		def get_messages():
			now = datetime.now().date()
			message_stats = {'registered': [], 'unregistered': []}
			messages_reg_all = Message.objects.all()
			messages_unreg_all = UnregisteredMessage.objects.all()
			for n in DAY_VALUES:
				start_day = now - timedelta(n)
				message_stats['registered'].append(messages_reg_all
					.filter(sent_at__range=(start_day, now)).count())
				message_stats['unregistered'].append(messages_unreg_all
					.filter(sent_at__range=(start_day, now)).count())
			message_stats['registered'].append(messages_reg_all.count())
			message_stats['unregistered'].append(messages_unreg_all.count())
			return message_stats

		def get_source():
			how_did_you_find_us_stats = []
			for item in Client.LINK_SOURCE_CHOICES:
				how_did_you_find_us_stats.append({'name': item[1],
					'total': Client.objects.filter(link_source=item[0]).count()})
			return how_did_you_find_us_stats

		def get_weekstat():
			NUM_WEEKS = 5
			now = datetime.now().date()
			weekstat = {}
			for week in range(0, NUM_WEEKS):
				start_week = now - timedelta(weeks=week + 1)
				end_week = start_week + timedelta(days=7)
				weekstat['week_%s' % week] = [
					start_week,
					end_week - timedelta(days=1)]

				providers_all = (Healer.objects
					.filter(user__is_active=True,
							user__date_joined__range=[start_week, end_week])
					.count())
				providers_complete = (Healer.objects
					.filter(user__is_active=True, pk__in=healers_complete,
							user__date_joined__range=[start_week, end_week])
					.count())
				weekstat['week_%s_all' % week] = providers_all
				weekstat['week_%s_complete' % week] = providers_complete

				clients = (Client.objects
					.filter(user__is_active=True,
							user__date_joined__range=[start_week, end_week])
					.exclude(id__in=providers)
					.count())
				weekstat['week_%s_clients' % week] = clients

				appointments = (Appointment.objects.without_relations()
					.filter(created_date__range=[start_week, end_week])
					.count())
				weekstat['week_%s_appointments' % week] = appointments
			return weekstat

		def get_30_day_user_stats():
			NUM_DAYS = 30
			now = datetime.now().date()
			daystat = {'n': [], 'all': [], 'complete': [],
						'clients': [], 'appointments': []}
			for n in range(1, NUM_DAYS + 1):
				start_day = now - timedelta(n)
				end_day = start_day + timedelta(1)
				all = (Healer.objects
					.filter(user__is_active=True,
						user__date_joined__range=[start_day, end_day])
					.count())
				complete = (Healer.objects
					.filter(user__is_active=True, pk__in=healers_complete,
						user__date_joined__range=[start_day, end_day])
					.count())
				clients = (Client.objects
					.filter(user__is_active=True,
						user__date_joined__range=[start_day, end_day])
					.exclude(id__in=providers).count())
				appointments = (Appointment.objects.without_relations()
					.filter(created_date__range=[start_day, end_day]).count())
				daystat['n'].append(n)
				daystat['all'].append(all)
				daystat['complete'].append(complete)
				daystat['clients'].append(clients)
				daystat['appointments'].append(appointments)
			return daystat

		def get_posts_and_videos_stats():
			now = datetime.now().date()
			daystat = {'posts_all': [], 'posts_published': [], 'videos': []}
			posts_all_total = BlogPost.objects.all()
			posts_published_total = posts_all_total.filter(status=2)
			videos_total = ClientVideo.objects.all()
			for n in DAY_VALUES:
				start_day = now - timedelta(n)
				posts_all = posts_all_total.filter(publish_date__range=(start_day, now)).count()
				posts_published = posts_published_total.filter(publish_date__range=(start_day, now)).count()
				videos = videos_total.filter(date_added__range=(start_day, now)).count()
				daystat['posts_all'].append(posts_all)
				daystat['posts_published'].append(posts_published)
				daystat['videos'].append(videos)
			daystat['posts_all'].append(posts_all_total.count())
			daystat['posts_published'].append(posts_published_total.count())
			daystat['videos'].append(videos_total.count())
			return daystat

		def get_invs():
			# ['2',] maybe more statuses?
			invs = {}

			all_invitations = SiteJoinInvitation.objects.filter(status__in=['2', ])
			client_invitations = SiteJoinInvitation.objects.filter(is_to_healer=False, status__in=['2', ])
			provider_invitations = SiteJoinInvitation.objects.filter(is_to_healer=True, status__in=['2', ])

			invs['all_total'] = all_invitations.count()
			invs['all_dated'] = (all_invitations
				.filter(sent__range=[start_date, timezone.now()])
				.extra({'day': "(EXTRACT (DAY FROM (now() - sent)))"})
				.values('day')
				.annotate(qty=Count('id')))

			invs['client_total'] = client_invitations.count()
			invs['client_dated'] = (client_invitations
				.filter(sent__range=[start_date, timezone.now()])
				.extra({'day': "(EXTRACT (DAY FROM (now() - sent)))"})
				.values('day')
				.annotate(qty=Count('id')))

			invs['provider_inv_total'] = provider_invitations.filter(create_friendship=False).count()
			invs['provider_inv_dated'] = (provider_invitations
				.filter(create_friendship=False, sent__range=[start_date, timezone.now()])
				.extra({'day': "(EXTRACT (DAY FROM (now() - sent)))"})
				.values('day')
				.annotate(qty=Count('id')))

			invs['provider_rec_total'] = provider_invitations.filter(create_friendship=True).count()
			invs['provider_rec_dated'] = (provider_invitations
				.filter(create_friendship=True, sent__range=[start_date, timezone.now()])
				.extra({'day': "(EXTRACT (DAY FROM (now() - sent)))"})
				.values('day')
				.annotate(qty=Count('id')))

			invs['referrals_total'] = ReferralsSent.objects.all().count()
			invs['referrals'] = (ReferralsSent.objects
				.filter(date_sent__range=[start_date, timezone.now()])
				.extra({'day': "(EXTRACT (DAY FROM (now() - date_sent)))"})
				.values('day')
				.annotate(qty=Count('id')))

			invs['all_dated'] = calculate_daily_inv(invs['all_dated'])
			invs['client_dated'] = calculate_daily_inv(invs['client_dated'])
			invs['provider_inv_dated'] = calculate_daily_inv(invs['provider_inv_dated'])
			invs['provider_rec_dated'] = calculate_daily_inv(invs['provider_rec_dated'])
			invs['referrals'] = calculate_daily_inv(invs['referrals'])
			return invs

		def get_stats_dated(objects):
			def convert_to_dated(providers):
				output = {}
				now = datetime.now().date()
				for n in DAY_VALUES:
					start_date = now - timedelta(n)
					providers_count = providers.filter(
						user__date_joined__range=[start_date, now]).count()
					output['day%d' % n] = providers_count
				return output
				#  \
				# .extra({'day': "(EXTRACT (DAY FROM (now() - \"auth_user\".\"date_joined\")))"}) \
				# .values('day') \
				# .annotate(qty=Count('id'))

				# return calculate_daily_inv(providers)
			return {
				'count': objects.count(),
				'dated': convert_to_dated(objects),
			}

		def get_stats_daily(objects, created=False, added=False,
							created_reversed=False):
			def get_filter():
				if added:
					return 'added__range'
				elif created:
					return 'date_created__range'
				elif created_reversed:
					return 'created_date__range'

				return 'user__date_joined__range'

			def get_extra():
				if added:
					return {'day': '(EXTRACT (DAY FROM (now() - added)))'}
				elif created:
					return {'day': '(EXTRACT (DAY FROM (now() - date_created)))'}
				elif created_reversed:
					return {'day': '(EXTRACT (DAY FROM (now() - created_date)))'}

				return {'day': '(EXTRACT (DAY FROM (now() - "auth_user"."date_joined")))'}

			def get_count_id_name():
				if created:
					return 'user_assoc'
				return 'id'

			return {'count': objects.count(),
				'dated': calculate_daily_inv(objects
					.filter(**{get_filter(): [start_date, timezone.now()]})
					.extra(get_extra())
					.values('day')
					.annotate(qty=Count(get_count_id_name())))}

		providers = Healer.objects.all().order_by('-id')
		healers_complete = Healer.complete.values_list('id', flat=True)
		start_date = timezone.now() - timezone.timedelta(days=365)
		wellness_centers_all = WellnessCenter.objects.filter(user__is_active=True)
		wellness_centers_complete = wellness_centers_all.filter(pk__in=healers_complete)
		providers_all = (Healer.objects
			.filter(user__is_active=True)
			.exclude(pk__in=wellness_centers_all))
		providers_complete = (providers_all
			.filter(pk__in=healers_complete)
			.exclude(pk__in=wellness_centers_complete))
		providers_blank_about = providers_all.filter(about='')
		providers_blank_location = providers_all.filter(clientlocation__isnull=True)
		providers_blank_avatar = providers_all.filter(user__avatar__isnull=True)
		providers_using_schedule = providers_complete.filter(scheduleVisibility=Healer.VISIBLE_EVERYONE)
		facebook_imports = (UserAssociationDated.objects
			.filter(user_assoc__user__id__in=providers, user_assoc__service='facebook'))
		google_imports = (UserAssociationDated.objects
			.filter(user_assoc__user__id__in=providers, user_assoc__service='google'))
		clients = Client.objects.filter(user__is_active=True).exclude(id__in=providers)
		healers_with_notes = (Healer.objects.all()
			.annotate(number_of_notes=Count('notes'))
			.filter(number_of_notes__gt=0))
		stripe_connect_users = UserAssociation.objects.filter(service='stripe').values_list('user', flat=True)
		stripe_connect_healers = Healer.objects.filter(user__in=stripe_connect_users)

		payments = Payment.objects.all()
		payments_healers = payments.values_list('appointment__healer', flat=True).distinct()
		payments_all = []
		for healer in payments_healers:
			payments_all.append((Healer.objects.get(pk=healer), payments.filter(appointment__healer=healer).aggregate(total_charge=Sum('amount')).values()[0]))
		payments_all = sorted(payments_all, key=lambda tup: tup[1], reverse=True)

		stats = {
			'top_city_searches': (filter_last_30_days(Zipcode.objects.all(), 'healersearchhistory', 'created_at')
				.annotate(num_of_searches=Count('healersearchhistory'))
				.exclude(num_of_searches=0).order_by('-num_of_searches')[:10]),
			'top_modality_searches': (filter_last_30_days(Modality.objects_approved.all(), 'healersearchhistory', 'created_at')
				.annotate(num_of_searches=Count('healersearchhistory'))
				.exclude(num_of_searches=0).order_by('-num_of_searches')[:10]),
			'healers_with_most_appointments': (filter_last_30_days(Healer.objects.all(), 'healer_appointments', 'created_date')
				.annotate(num_appointments=Count('healer_appointments'))
				.order_by('-num_appointments')[:10]),
			'specialties_top10': get_specialties_top10(),
			'specialties_categories': get_specialties_categories(),
			'healers_in_zip': get_healers_in_zip(),
			'intake_form_stats': get_intake_form(),
			'messages': get_messages(),
			'source': get_source(),
			'weekstat': get_weekstat(),
			'users_daystat': get_30_day_user_stats(),
			'posts_and_video_daystat': get_posts_and_videos_stats(),
			'invs': get_invs(),
			'wellness_centers_all': get_stats_dated(wellness_centers_all),
			'providers_all': get_stats_dated(providers_all),
			'wellness_centers_complete': get_stats_dated(wellness_centers_complete),
			'providers_complete': get_stats_dated(providers_complete),
			'providers_blank_about': get_stats_daily(providers_blank_about),
			'providers_blank_location': get_stats_daily(providers_blank_location),
			'providers_blank_avatar': get_stats_daily(providers_blank_avatar),
			'providers_using_schedule': get_stats_daily(providers_using_schedule),
			'recommendations': get_stats_daily(Referrals.objects, added=True),
			'facebook_imports': get_stats_daily(facebook_imports, created=True),
			'google_imports': get_stats_daily(google_imports, created=True),
			'clients': get_stats_daily(clients),
			'appointments': get_stats_daily(
				Appointment.objects.without_relations(), created_reversed=True),
			'hr': {
				'requests_count': HealingRequest.objects.count(),
				'searches_count': HealingRequestSearch.objects.count(),
				'saved_searches_count': HealingRequestSearch.objects.filter(saved=True).count(),
				'people_contacted_count': MessageExtra.objects.filter(
					source=MessageExtra.SOURCE_CHOICE_HR).distinct('message').count(),
			},
			'notes': {
				'healers_with_most_notes': (healers_with_notes
					.order_by('-number_of_notes')[:10]),
				'total_number_of_notes': Note.objects.all().count(),
				'number_of_healers_with_notes': healers_with_notes.count(),
				'number_of_healers_with_more_than_seven_notes': healers_with_notes.filter(number_of_notes__gt=7).count()
			},
			'stripe': {
				'stripe_connect_users_count': stripe_connect_users.count(),
				'stripe_connect_percentage_fee': stripe_connect_healers.filter(
					booking_healersource_fee=Healer.BOOKING_HEALERSOURCE_FEE_PERCENTAGE).count(),
				'stripe_connect_fixed_fee': stripe_connect_healers.filter(
					booking_healersource_fee=Healer.BOOKING_HEALERSOURCE_FEE_FIXED).count(),
				'stripe_connect_total_amount': Payment.objects.all().aggregate(Sum('amount')).values()[0] / 100,
				'gc_enabled_total': Healer.objects.filter(gift_certificates_enabled=True).count(),
				'BOOKING_HEALERSOURCE_FEE': settings.BOOKING_HEALERSOURCE_FEE,
			},
			'ghp': {
				'total_healing_sent': SentHealing.total_healing_sent(),
				'number_of_members': ghp_members().count(),
			},
			'phonegap_registrations_number': Client.objects.filter(
				signup_source=Client.SIGNUP_SOURCE_APP).count(),
			'ambassador': {
				'top_five': (Client.objects
					.exclude(ambassador=None)
					.annotate(number_of_signed_up_users=Count('ambassador'))
					.order_by('-number_of_signed_up_users')[:5]),
				'total': Client.objects.filter(ambassador_program=True).count(),
				'number_of_signed_up_users': Client.objects.exclude(ambassador=None).count(),
			},
			'payments_notes_subscriptions_total': Customer.objects.exclude(payment_notes=0).count(),
			'payments_all': payments_all
		}
		return providers[:50], stats

	message = ""
	point = None

	query = request.GET.copy()
	remote_sessions = query.pop('remote_sessions', [False])[0]
	exclude_centers = query.pop('exclude_centers', [False])[0]

	if city is not None:
		if search_top_cities.get(city, False) is not False:
			point = Zipcode.objects.filter(
				code=search_top_cities.get(city))[0]
			query.update({
				'zipcode': point.code,
				'city':  point.city,
				'state': point.state,
				'search_city_or_zipcode': '%s %s' % (point.city, point.state)
			})
		else:
			if city != 'all':
				point = Zipcode.objects.filter(city=city)
				if state is not None:
					point = point.filter(state=state)
				if len(point) > 0:
					query.update({
						'zipcode': point[0].code,
						'city':  point[0].city,
						'state': point[0].state,
						'search_city_or_zipcode': '%s %s' % (point[0].city,
															point[0].state)
					})
				else:
					raise Http404

	city_select_code = get_city_select_code(query)

	if specialty is not None:
		if specialty in map(slugify, search_top_specialties):
			idx = map(slugify, search_top_specialties).index(specialty)
			modality = Modality.objects_approved.filter(
				title=search_top_specialties[idx])[0]
			query.update({
				'modality_id': modality.pk,
				'modality': modality.title
			})
		elif specialty in map(slugify, search_top_categories):
			idx = map(slugify, search_top_categories).index(specialty)
			category = ModalityCategory.objects.filter(
				title=search_top_categories[idx])[0]
			query.update({
				'modality_category_id': category.pk,
				'modality': category.title,
			})
		else:
			category = ModalityCategory.objects.filter(title=specialty)
			if len(category) > 0:
				query.update({
					'modality_category_id': category[0].pk,
					'modality': category[0].title,
				})
			else:
				modality = Modality.objects_approved.filter(title=specialty)
				if len(modality) > 0:
					query.update({
						'modality_id': modality[0].pk,
						'modality': modality[0].title
					})
				else:
					raise Http404

	if query.get('modality_id', False):
		query['modality3'] = 'c:' + str(query['modality_id'])
	if query.get('modality_category_id', False):
		query['modality3'] = 'p:' + str(query['modality_category_id'])

	if not query.get('search_city_or_zipcode', False):
		query['search_city_or_zipcode'] = 'Everywhere'

	form = HealerSearchForm(query or None)

	zipcode = modality_category_id = modality_id = concierge = concierge_city = concierge_form = None
	providers = []
	if form.is_valid() and not all:
		point, zipcode, message = process_zipcode(form, request)

		modality_category_id = form.cleaned_data.get('modality_category_id')
		modality_id = form.cleaned_data.get('modality_id')

		if modality_id:
			modality = Modality.objects_approved.filter(id=modality_id)[0]
		elif modality_category_id:
			modality = ModalityCategory.objects.filter(id=modality_category_id)[0]

		name_or_email = form.cleaned_data.get('name_or_email')

		request.session['search_state'] = form.cleaned_data

		if not message or settings.DEBUG:
			filter_by_referral = None
			if embed_user and not embed_user.client.embed_search_all:
				filter_by_referral = embed_user
			providers, more = get_healers_geosearch(
				request, None, point, modality_category_id, modality_id,
				name_or_email, remote_sessions=remote_sessions,
				exclude_centers=exclude_centers,
				filter_by_referral=filter_by_referral)
			concierge, concierge_city = get_concierge_and_city()
			if concierge is not None:
				concierge_form = ConciergeForm(request.POST or None)
				if concierge_form.is_valid():
					concierge_form.email_data(concierge.user)
					if request.user.is_authenticated() and concierge.has_intake_form():
						concierge.send_intake_form(request.user.client)
						request.session['concierge_request'] = True
						return redirect(reverse('intake_form_answer', args=[concierge.username()]))
					else:
						return redirect(reverse('concierge_thanks', args=[concierge.username()]))
	else:
		request.session['point'] = None
		modality_id = modality
		name_or_email = None
		form = HealerSearchForm(initial=request.session.get('search_state', None))

	stats = None
	if all:
		if request.user.is_superuser or request.user.is_staff:
			providers, stats = get_stats()
		else:
			raise Http404

	embed = None
	if embed_user:
		embed = {
			'username': embed_user.username,
			'background_color': embed_user.client.embed_background_color
		}

	search_display_type = request.GET.get('search_display_type', 'list')
	ctx = {
		'stats': stats,
		"search_form": form,
		'search_display_type': search_display_type,
		"found_providers": providers,
		"message": message,
		"modality_id": modality_id,
		"modality_category_id": modality_category_id,
		"modality": modality,
		"zipcode": zipcode,
		'all': all,
		'skip_first_hr': skip_first_hr,
		'city_select_code': city_select_code,
		'concierge': concierge,
		'concierge_city': concierge_city,
		'concierge_form': concierge_form,
		'remote_sessions': remote_sessions,
		'embed': embed,
		'phonegap': phonegap,
	}

	return render_search(ctx, request, template_name)


def process_zipcode(form, request):

	point = None
	message = None

	zipcode = form.get_zipcode()
	if zipcode:
		point = zipcode.point
		request.session['point'] = point
		request.session['zipcode'] = zipcode.code

	else:
		request.session['zipcode'] = ""

		#		if not point: #and not settings.DEBUG:
		request.session['point'] = None

		if form.cleaned_data['zipcode'] and form.cleaned_data['zipcode'] != '0':
			message = "Could not find zipcode %s" % form.cleaned_data['zipcode']

	user_agent = request.META.get('HTTP_USER_AGENT')
	if user_agent and user_agent.find('compatible') == -1:
		add_to_healer_search_history(form.data.copy(), request.user, zipcode)

	return point, zipcode, message


def tour(request, template_name="about/tour.html"):
	client_signup_form = ClientSignupForm()
	form = client_signup_form

	return render_to_response(template_name, {
		"client_signup_form": client_signup_form,
		"form": form,
	}, context_instance=RequestContext(request))


def healers_complete_combiner(healers, healers_comp):
	sp = defaultdict(dict)
	for dd in (healers, healers_comp):
		for d in dd:
			if 'healers' not in sp[d['title']]:
				sp[d['title']].update({'healers': 0})
			if 'healers_c' not in sp[d['title']]:
				sp[d['title']].update({'healers_c': 0})
			sp[d['title']].update(d)
	return sorted([d[1] for d in sp.items()], key=lambda k: k['healers'],
				  reverse=True)


def calculate_daily_inv(inv_dated):
	"""
	makes a dict for invitations sum 1,2,3,7,14.... days ago period
	"""
	#boilerpalte for invitations per day
	empty_dates = [{'day': d, 'qty': 0} for d in range(1, 366)]
	dt = defaultdict(dict)
	for dd in (empty_dates, inv_dated):
		for d in dd:
			dt[d['day']].update(d)
	inv_dated_final = {
		'day1': 0,
		'day2': 0,
		'day3': 0,
		'day7': 0,
		'day14': 0,
		'day30': 0,
		'day60': 0,
		'day90': 0,
		'day180': 0,
		'day365': 0,
	}

	tsum = 0
	for cid in dt.values():
		tsum += cid['qty']
		for d_value in DAY_VALUES:
			if cid['day'] <= d_value:
				inv_dated_final['day%s' % d_value] = tsum
				break

	return inv_dated_final


@user_authenticated
def all_users(request, healers_only=False, center_clients_only=False, **kwargs):
	if not request.user.is_superuser and (healers_only or not center_clients_only):
		raise Http404

	fname_str = ''
	if healers_only:
		profiles = Healer.objects.all().order_by('-user__date_joined')

		if kwargs.pop('boston', False):
			print Zipcode.objects.get(code='02134').point
			profiles = Healer.objects.filter(clientlocation__location__point__distance_lte=(Zipcode.objects.get(code='02134').point, D(mi=100)) ).distinct()

		fname_str = 'Healers'
	else:
		if center_clients_only:
			profiles = sorted([o['friend'].client for o in Clients.objects.friends_for_user(request.user)], key=lambda k: k.user.first_name)
		else:
			profiles = Client.objects.filter(user__is_active=True).order_by('-user__date_joined')

		fname_str = 'Clients'

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="All_%s_%s.csv"' % (fname_str, str(datetime.today()).split(' ')[0])

	writer = UnicodeWriter(response)

	for p in profiles:
		u = p.user
		writer.writerow([unicode(u.first_name), unicode(u.last_name), unicode(u.email), get_account_type(u), unicode(u.date_joined)])

	return response


def concierge_thanks(request, username):
	concierge = Concierge.objects.get(user__username='center')
	message = render_to_string(
						'about/concierge_thanks_message.html',
						{'name': concierge.user.get_full_name()})
	return render_to_response('about/concierge_thanks.html', {
		'thanks_message': message
	}, context_instance=RequestContext(request))


def render_notes_landing(extra_context, request=None):
	template = 'landing_pages/notes.html'
	ctx = {
		'images': sorted(os.listdir(settings.LANDING_NOTES_ROOT)),
		'signup_form': ClientSignupForm(),
	}
	return render_page(request, template, ctx, extra_context)


@utm_tracking
def landing_page_notes(request):
	tracking_code_update = request.session.get('tracking_code', {})

	tracking_code = settings.TRACKING_CODES['notes_landing']
	tracking_code.update(tracking_code_update)
	request.session['tracking_code'] = tracking_code
	request.session['notes_lp'] = True
	return render_notes_landing({}, request)


@utm_tracking
def landing_page_book(request):
	return render_to_response('landing_pages/book.html', {
	}, context_instance=RequestContext(request))


def render_book_thanks(extra_context, request=None):
	ctx = {'thanks_message': render_to_string('about/book_download.html')}
	if (request is not None and
			request.META.get('HTTP_REFERER', '') == get_full_url('landing_page_book')):
		ctx['tracking_code'] = settings.TRACKING_CODES['book_landing']
	template = 'account/thanks.html'
	return render_page(request, template, ctx, extra_context)


def book_thanks(request):
	return render_book_thanks({}, request)


def render_error_report(extra_context, request=None):
	ctx = {}
	template = 'about/error_report.html'
	return render_page(request, template, ctx, extra_context)


def error_report(request):
	return render_error_report({}, request)


@cache_page(60 * 60 * 24)
def featured(request):
	def get_centers():
		centers = list(WellnessCenter.objects.all())
		centers.sort(key=lambda x: len(x.get_healers_in_wcenter()), reverse=True)
		return centers[:5]

	session = request.session.get('search_state', None)
	form = HealerSearchForm(initial=session)

	point = request.session.get('point', None)
	providers = get_healers_geosearch(request, point=point,
		schedule_visibility=Healer.VISIBLE_EVERYONE, exclude_centers=True)[0]

	centers = get_centers()

	return render_to_response(
		'about/featured.html', {
			'search_form': form,
			'found_providers': providers,
			'centers': centers,
			'compose_form': ComposeFormUnregistered(),
		}, context_instance=RequestContext(request, {}))


def pricing(request):
	def get_healers():
		healers = list(Healer.complete.all().select_related('user'))
		random.shuffle(healers)
		return healers

	return render_to_response(
		'about/pricing.html', {
			'healers': get_healers(),
			'client_signup_form': ClientSignupForm(),
		}, context_instance=RequestContext(request, {}))


@cache_page(60 * 60 * 24)
def learn(request, only_posts=False):
	def get_clients_for_videos_list():
		"""Return 5 Clients. One client - username 'healersource_tv', others - sorted by number of videos desc."""
		def filter_videos(qset):
			return qset.filter(videotype=ClientVideo.VIDEO_TYPE_CLIENT)

		def get_clients_with_videos():
			videos = ClientVideo.objects.all()
			videos = filter_videos(videos)
			clients = list(set(videos.values_list('client', flat=True)))
			return Client.objects.filter(pk__in=clients).exclude(pk=healersource_tv_client.pk)

		def get_clients_sorted_by_number_of_videos():
			clients_videos_number = [
				{'client': client,
				'number_of_videos': filter_videos(client.videos.all()).count()}
					for client in get_clients_with_videos()]
			clients_videos_number.sort(key=lambda x: x['number_of_videos'], reverse=True)
			return clients_videos_number[:4]

		def get_hs_tv_client_number_of_videos():
			videos = healersource_tv_client.videos.all()
			return filter_videos(videos).count()

		healersource_tv_client = Client.objects.get(user__username='healersource_tv')

		return [{'client': healersource_tv_client,
			'number_of_videos': get_hs_tv_client_number_of_videos()}] + get_clients_sorted_by_number_of_videos()

	def get_top_bloggers():
		"""Return 5 top bloggers."""
		def get_users_with_posts():
			posts = blogposts.distinct()
			users = list(set(posts.values_list('user', flat=True)))
			return User.objects.filter(pk__in=users)

		users_number_of_articles = [{'user': user, 'number_of_articles': user.blogposts.count()} for user in get_users_with_posts()]
		users_number_of_articles.sort(key=lambda x: x['number_of_articles'], reverse=True)

		# return User.objects.annotate(number_of_articles=Count('blogposts')).order_by('-number_of_articles')[:5]
		return users_number_of_articles[:5]

	complete_users = Healer.complete.all().values_list('user', flat=True)
	blogposts = BlogPost.objects.published().filter(user__in=complete_users)
	posts = blogposts.order_by('-publish_date').distinct()

	ctx = {'posts': posts}
	if not only_posts:
		ctx.update({
			'clients_for_videos_list': get_clients_for_videos_list(),
			'top_bloggers': get_top_bloggers(),
		})
	return render_to_response(
		'about/learn.html', ctx, context_instance=RequestContext(request, {}))


class SearchAjax(APIView):
	def get(self, request, format=None):
		try:
			display_type = request.GET.get('display_type', 'list')
			embed_user = request.GET.get('embed_user', False)
			phonegap = json.loads(request.GET.get('phonegap', 'false'))
		except:
			return HttpResponseBadRequest()

		if embed_user:
			embed_user = User.objects.get(username__exact=embed_user)
		response = search(
			request,
			template_name='about/search/results_%s.html' % display_type,
			skip_first_hr=True,
			embed_user=embed_user,
			phonegap=phonegap)
		return Response(response.content)


class CitySelectCode(APIView):
	def get(self, request, format=None):
		try:
			query = json.loads(request.GET['query'])
		except:
			return HttpResponseBadRequest()

		return Response(get_city_select_code(query))


class FeaturedProviders(APIView):
	"""Return html blocks with featured providers for homepage."""
	def get(self, request, format=None):
		try:
			featured_providers = request.GET['featured_providers']
		except:
			return HttpResponseBadRequest()

		available_providers = get_featured_providers()
		try:
			featured_providers = json.loads(featured_providers)
		except ValueError:
			return HttpResponseBadRequest()
		result = ''
		for provider in featured_providers:
			if provider in available_providers:
				try:
					provider = Healer.objects.get(user__username__iexact=provider)
					is_schedule_visible = provider.is_schedule_visible(request.user)
					result += render_to_string(
						'about/homepage_featured_provider.html',
						{
							'featured_provider': provider,
							'is_schedule_visible': is_schedule_visible,
							'hide': True,
						})
				except Healer.DoesNotExist:
					pass
		return Response(result)


class GeoSpecialties(APIView):
	def get(self, request, format=None):
		geo = int(request.GET.get('geo', False))
		healers_complete = Healer.complete
		if geo:
			zipcode = Zipcode.objects.get(pk=geo)
			healers = healers_complete.within_50_miles(zipcode)

			if len(healers) == 0:
				return Response()
		else:
			healers = healers_complete

		healers = healers.values_list('pk', flat=True)

		modalities = Modality.objects_approved.prefetch_related('category')

		if len(healers) > 0:
			modalities = modalities.filter(healer__pk__in=healers)

		modalities = modalities.order_by('title').distinct()

		categories = {}
		categories_tree = {}
		for modality in modalities:
			for category in modality.category.all():
				categories.update({
					category.title: category.pk
				})
				if not categories_tree.get(category.title, False):
					categories_tree[category.title] = []
				if modality not in categories_tree[category.title]:
					categories_tree[category.title].append(modality)

		categories_tree = sorted(categories_tree.iteritems(), key=operator.itemgetter(0))

		out = '<option selected="selected" value="">Any Specialty</option>'
		for cat in categories_tree:
			out += '<optgroup label="%s">' % cat[0]
			out += '<option value="p:%s">Any type of %s</option>' % (categories[cat[0]], cat[0])

			for spec in cat[1]:
				out += '<option value="c:%s">%s</option>' % (spec.pk, spec.title)
			out += '</optgroup>'

		return Response(out)


class ContactUs(APIView):
	def post(self, request, format=None):
		try:
			data = QueryDict(request.POST['data'])
		except:
			return HttpResponseBadRequest()

		from_ = '%s <%s>' % (data['name'], data['email'])
		send_hs_mail('Contact Us message', "about/contact_us.txt",
			{'message': data['message']}, from_, ['sales@healersource.com'])
		return Response()


class EmailConfirmationRequiredView(TemplateView):
	template_name = 'about/confirmation_required.html'

	def get_context_data(self, **kwargs):
		context = super(EmailConfirmationRequiredView, self).get_context_data(**kwargs)
		context.update(kwargs)
		return context
