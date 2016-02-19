from random import random
from datetime import datetime
import json
import facebook

from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings


from rest_framework.response import Response
from rest_framework.views import APIView

from oauth_access.models import UserAssociation

from util import full_url, absolute_url
from phonegap.utils import render_page
from friends.models import Contact
from clients.models import Client
from clients.utils import client_pic, get_person_content_type
from contacts_hs.models import ContactSocialId
from account_hs.views import UserAuthenticated
from account_hs.authentication import user_authenticated

import healers
from .models import SentHealing, GhpSettings, HealingPersonStatus, Phrase
from .utils import (favorites_exist, skipped_exist,
	ghp_members, person_status_exists)


def render_ghp_home(extra_context, request=None):
	template = 'send_healing/home.html'
	if request is not None and not request.user.is_authenticated():
		ctx = {}
	else:
		ctx = {
			'send_healing_url': full_url(reverse('send_healing')),
			'required_scopes': settings.OAUTH_ACCESS_SETTINGS['facebook']['endpoints']['provider_scope'],
			'scopes_to_check': settings.OAUTH_ACCESS_SETTINGS['facebook']['endpoints']['scopes_to_check'],
			'phrases': json.dumps(list(Phrase.objects.all().values_list('text', flat=True))),
		}
	return render_page(request, template, ctx, extra_context)


@user_authenticated
def send_healing_to_person(request, username):
	return home(request, get_object_or_404(User, username=username).client.pk)


def home(request, client_id=None):
	extra_context = {}
	if client_id is not None:
		extra_context['send_to_user'] = client_id
	if request.user.is_authenticated():
		extra_context['facebook_friends_exist'] = request.user.contacts.filter(contactsocialid__service='facebook').exists()

	def call_api_view(view_class):
		return view_class.as_view()(request, format='json').render().content

	extra_context['initial_data'] = call_api_view(LoadInitialData)
	extra_context['history'] = call_api_view(History)
	extra_context['settings'] = call_api_view(LoadSettings)
	extra_context['total_healing_sent'] = call_api_view(TotalHealingSent)

	return render_ghp_home(extra_context, request)


def facebook_healing(request, associate_new_account=False):
	request.session["send_healing_facebook"] = True
	if associate_new_account:
		request.session["facebook_associate_new_account"] = True
	return redirect(reverse("oauth_access_login", args=["facebook"]))


def get_healing(time, number_of_people, connection_string):
	if time:
		return '%s %s %s people' % (time, connection_string, number_of_people)
	return 'none yet'


class TotalHealingSent(APIView):
	def get(self, request, format=None):
		sent_time = SentHealing.total_healing_sent()
		sent_to_num_people = SentHealing.total_healing_sent_to_num_people()
		total_sent = get_healing(sent_time, sent_to_num_people, 'to')
		return Response(total_sent)


class LoadInitialData(APIView):
	def get(self, request, format=None):
		def get_token():
			try:
				return user.userassociation_set.get(service='facebook').token
			except UserAssociation.DoesNotExist:
				return ''

		def healing_sent_to_points():
			def get_healer_point():
				locations = healer.get_locations_objects()
				for location in locations:
					point = location.point
					if point is not None:
						return [point[1], point[0]]

			objects = SentHealing.objects.all().order_by('-created')
			points = []
			for obj in objects:
				if obj.person is None:
					continue
				contact_content_type = ContentType.objects.get(app_label='friends', model='contact')
				if obj.person_content_type == contact_content_type:
					try:
						social_obj = obj.person.contactsocialid_set.filter(service='facebook')[0]
						#REASON:
						# contactsocialid_set.filter(
						# service='facebook')[0]
						# using filter[0] instead of get, because, currently some contacts has multiple contactsocialids of same service 'facebook'
						if social_obj.point:
							l = list(social_obj.point.tuple)
							points.append(l)

					except IndexError, ContactSocialId.DoesNotExist:
						pass
				else:
					healer = healers.utils.is_healer(obj.person.user)
					if healer:
						point = get_healer_point()
						if point is not None:
							points.append(point)

				if len(points) == settings.SH_NUMBER_OF_LOCATIONS_ON_MAP:
					break
			return points

		user = request.user
		if not user.is_authenticated():
			return Response({'is_anonymous': True,
				'locations': healing_sent_to_points()})
		client = Client.objects.get(user=user)
		data = {
			'facebook_friends_exist': user.contacts.filter(contactsocialid__service='facebook').exists(),
			'favorites_exist': favorites_exist(client),
			'skipped_exist': skipped_exist(client),
			'token': get_token(),
			'locations': healing_sent_to_points(),
			'history_exists': SentHealing.objects.filter(sent_by=client).exists(),
			'healing_sent': get_healing(client.healing_sent(), client.healing_sent_to_num_people(), 'to'),
			'healing_received': get_healing(client.healing_received(), client.healing_received_from_num_people(), 'from'),
			'user_has_avatar': user.avatar_set.exists(),
		}
		return Response(data)


class History(UserAuthenticated):
	def get(self, request, format=None):
		user = request.user
		client = Client.objects.get(user=user)
		history = SentHealing.objects.filter(sent_by=client).order_by('-created')
		url_history = absolute_url(reverse('send_healing_ajax_history'))
		data = render_to_string('send_healing/history.html', {'history': history, 'url_history': url_history}, RequestContext(request))
		return Response(data)


def get_status(type):
	if type == 'skipped':
		return HealingPersonStatus.TO_SKIP
	elif type == 'favorite':
		return HealingPersonStatus.FAVORITE


class List(UserAuthenticated):
	def get(self, request, type, format=None):
		if type == 'skipped':
			action = 'Unskip'
			class_ = 'unskip'
		elif type == 'favorite':
			action = 'Remove'
			class_ = 'favorite'

		client = Client.objects.get(user=request.user)
		person_statuses = list(HealingPersonStatus.objects.filter(client=client,
			status=get_status(type)))
		person_statuses.sort(key=lambda x: x.full_name())
		context = {
			'action': action,
			'class': class_,
			'person_statuses': person_statuses
			}
		html = render_to_string('send_healing/status_list.html', context)
		return Response(html)


class RemoveStatus(UserAuthenticated):
	def post(self, request, type, id, format=None):
		client = Client.objects.get(user=request.user)
		person_status = get_status(type)
		HealingPersonStatus.objects.filter(client=client, status=person_status, id=id).delete()
		return Response(person_status_exists(client, person_status))


class SaveSettings(APIView):
	def post(self, request, format=None):
		send_to_ghp_members = json.loads(request.POST['send_to_ghp_members'])
		send_to_my_favorites_only = json.loads(request.POST['send_to_my_favorites_only'])
		i_want_to_receive_healing = json.loads(request.POST['i_want_to_receive_healing'])

		if request.user.is_authenticated():
			ghp_settings = GhpSettings.objects.get_or_create(user=request.user)[0]
			ghp_settings.send_to_ghp_members = send_to_ghp_members
			ghp_settings.send_to_my_favorites_only = send_to_my_favorites_only
			ghp_settings.i_want_to_receive_healing = i_want_to_receive_healing
			ghp_settings.save()
		else:
			request.session['send_to_ghp_members'] = send_to_ghp_members
			request.session['send_to_my_favorites_only'] = send_to_my_favorites_only
			request.session['i_want_to_receive_healing'] = i_want_to_receive_healing

		return Response()


class LoadSettings(APIView):
	def get(self, request, format=None):
		def get_settings():
			if request.user.is_authenticated():
				settings = GhpSettings.objects.get_or_create(user=request.user)[0]
				send_to_ghp_members = settings.send_to_ghp_members
				send_to_my_favorites_only = settings.send_to_my_favorites_only
				i_want_to_receive_healing = settings.i_want_to_receive_healing
			else:
				send_to_ghp_members = request.session.get('send_to_ghp_members', True)
				send_to_my_favorites_only = request.session.get('send_to_my_favorites_only', False)
				i_want_to_receive_healing = request.session.get('i_want_to_receive_healing', True)

			if (not (send_to_ghp_members or send_to_my_favorites_only or
					i_want_to_receive_healing)):
				return False, False, send_to_my_favorites_only, False
			else:
				return (send_to_ghp_members, send_to_my_favorites_only,
					i_want_to_receive_healing)

		settings = get_settings()
		settings = {
			'send_to_ghp_members': settings[0],
			'send_to_my_favorites_only': settings[1],
			'i_want_to_receive_healing': settings[2]}
		return Response(settings)


def set_status(client, type, id, person_status):
	healing_person_status = HealingPersonStatus.objects.get_or_create(client=client, person_content_type=type,
		person_object_id=id)[0]
	healing_person_status.status = person_status
	healing_person_status.save()


class AddFavorite(UserAuthenticated):
	def post(self, request, type, id, format=None):
		client = Client.objects.get(user=request.user)
		set_status(client, get_person_content_type(type), id, HealingPersonStatus.FAVORITE)
		return Response()


class SendHealingToPerson(APIView):
	def post(self, request, format=None):
		id = request.POST['id']
		type = request.POST['type']
		initial_load = json.loads(request.POST['initial_load'])
		specific_id = request.POST.get('specific_id', None)
		started_at = request.POST.get('started_at', None)
		ended_at = request.POST.get('ended_at', None)

		def get_next_random_person(type):
			def get_persons_healed_today(content_type):
				if request.user.is_authenticated():
					return client.sent_healing.filter(
						created__contains=datetime.today().date(), person_content_type=content_type)\
						.values_list('person_object_id', flat=True)
				else:
					return []

			def get_random_person(objects, content_type, exclude_persons_healed_today):
				if exclude_persons_healed_today:
					objects = objects.exclude(id__in=get_persons_healed_today(content_type))
				if ghp_settings.send_to_my_favorites_only:
					favorite_ids = HealingPersonStatus.objects.filter(client=client, status=HealingPersonStatus.FAVORITE,
						person_content_type=content_type).values_list('person_object_id', flat=True)
					objects = objects.filter(id__in=favorite_ids)

				return objects.order_by('?')

			def get_random_ghp_members(exclude_persons_healed_today):
				if request.user.is_authenticated():
					objects = ghp_members().exclude(pk=client.pk).exclude(pk__in=members_to_skip)
				else:
					objects = ghp_members()
				return get_random_person(objects, client_content_type, exclude_persons_healed_today)

			def get_fb_uid(contact):
				try:
					return contact.contactsocialid_set.filter(service='facebook')[0].social_id
				except IndexError:
					return ''

			def get_profile_url(type, obj):
				if type == 'contact':
					try:
						return obj.contactsocialid_set.filter(service='facebook')[0].fb_profile_url()
					except IndexError:
						pass
				else:
					if healers.utils.is_healer(obj.user):
						return obj.user.client.healer.healer_profile_url()

			def get_persons(exclude_persons_healed_today=True):
				random_ghp_members = random_facebook_friends = []
				if ghp_settings.send_to_ghp_members or ghp_settings.send_to_my_favorites_only:
					random_ghp_members = get_random_ghp_members(exclude_persons_healed_today)

				return random_ghp_members, random_facebook_friends

			def count_persons():
				number_of_members = number_of_facebook_friends = 0
				number_of_members = len(random_ghp_members)
				number_of_facebook_friends = len(random_facebook_friends)
				total = number_of_members + number_of_facebook_friends
				return (number_of_members, number_of_facebook_friends, total)

			def get_persons_ids_to_skip(content_type):
				return persons_to_skip.filter(person_content_type=content_type).values_list('person_object_id', flat=True)

			if specific_id is not None:
				if type == 'contact':
					model = Contact
				else:
					model = Client
				obj = model.objects.get(pk=specific_id)
			else:
				if request.user.is_authenticated():
					ghp_settings = GhpSettings.objects.get_or_create(user=client.user)[0]
				else:
					ghp_settings = GhpSettings(send_to_ghp_members=True)
				client_content_type = get_person_content_type('client')
				contact_content_type = get_person_content_type('contact')

				if request.user.is_authenticated():
					persons_to_skip = HealingPersonStatus.objects.filter(client=client, status=HealingPersonStatus.TO_SKIP)
				else:
					persons_to_skip = HealingPersonStatus.objects.none()
				members_to_skip = get_persons_ids_to_skip(client_content_type)
				facebook_friends_to_skip = get_persons_ids_to_skip(contact_content_type)
				random_ghp_members, random_facebook_friends = get_persons()
				number_of_members, number_of_facebook_friends, total = count_persons()
				if total == 0:
					random_ghp_members, random_facebook_friends = get_persons(False)
					number_of_members, number_of_facebook_friends, total = count_persons()

				if total == 0:
					return

				def get_member_as_next_person():
					"""Return True if next person should be a member.
						If # of friends > # ghp members, it uses %.
						If # of friends < # ghp members, it's 50/50."""

					if number_of_facebook_friends == 0:
						return True

					if number_of_facebook_friends > number_of_members:
						return random() < number_of_members / float(total)
					else:
						return random() < 0.5 and number_of_members != 0

				if get_member_as_next_person():
					type = 'client'
					obj = random_ghp_members[0]
				else:
					type = 'contact'
					obj = random_facebook_friends[0]

			next_random_person = {}
			if type == 'client':
				next_random_person['name'] = unicode(obj)
				next_random_person['first_name'] = obj.user.first_name
				next_random_person['fb_uid'] = ''
			else:
				next_random_person['name'] = obj.name
				next_random_person['first_name'] = obj.name.split(' ')[0]
				next_random_person['fb_uid'] = get_fb_uid(obj)

			next_random_person['obj'] = obj
			next_random_person['type'] = type
			next_random_person['id'] = obj.pk
			next_random_person['profile_url'] = get_profile_url(type, obj)
			next_random_person['profile_pic'] = client_pic(type, obj)
			if request.user.is_authenticated():
				next_random_person['is_favorite'] = HealingPersonStatus.objects.filter(
					client=client, person_content_type=get_person_content_type(type),
					person_object_id=obj.pk, status=HealingPersonStatus.FAVORITE).exists()
			else:
				next_random_person['is_favorite'] = False

			return next_random_person

		def send_facebook_notification(contact):
			pass
			# if settings.DEBUG:
			# 	return
			# notification = 'You have received healing via the HealerSource Healing Circle'
			# facebook_id = contact.contactsocialid_set.filter(service='facebook')[0].social_id
			# facebook_key = settings.OAUTH_ACCESS_SETTINGS['facebook']['keys']
			# access_token = facebook.get_app_access_token(facebook_key['KEY'], facebook_key['SECRET'])
			# graph = facebook.GraphAPI(access_token)
			# try:
			# 	graph.put_object(facebook_id, 'notifications', template=notification)
			# except facebook.GraphAPIError:
			# 	pass

		if not request.user.is_anonymous():
			client = Client.objects.get(user=request.user)

		skip = False
		if started_at is None:
			skip = True

		if not initial_load:
			person_content_type = get_person_content_type(type)
			obj = None
			if skip and not request.user.is_anonymous():
				set_status(client, person_content_type, id, HealingPersonStatus.TO_SKIP)
			else:
				if not request.user.is_anonymous():
					duration = int(request.POST['duration'])
					if duration >= settings.SH_MIN_DURATION:
						obj = SentHealing.objects.create(
							sent_by=client,
							person_object_id=id,
							person_content_type=person_content_type,
							started_at=datetime.strptime(started_at, "%a, %d %b %Y %H:%M:%S %Z"),
							ended_at=datetime.strptime(ended_at, "%a, %d %b %Y %H:%M:%S %Z"),
							duration=duration,
						)
						if type == 'contact':
							send_facebook_notification(obj.person)

		context = {}
		next_random_person = get_next_random_person(type)
		context['next_random_person'] = next_random_person
		context['send_healing_url'] = full_url(reverse('send_healing'))
		context['required_scopes'] = settings.OAUTH_ACCESS_SETTINGS['facebook']['endpoints']['provider_scope']
		context['scopes_to_check'] = settings.OAUTH_ACCESS_SETTINGS['facebook']['endpoints']['scopes_to_check']

		if not skip and not request.user.is_anonymous():
			context['sent_healing_history'] = SentHealing.objects.filter(
				sent_by=client).order_by("-created")

		result = {}
		if next_random_person:
			result['next_random_fb_uid'] = next_random_person['fb_uid']
			result['person_type'] = next_random_person['type']
			result['person_id'] = next_random_person['id']
			result['no_persons'] = False
		else:
			result['no_persons'] = True

		if not skip:
			if obj is not None:
				html = render_to_string("send_healing/healing_sent_page_obj.html", {'obj': obj})
			else:
				html = ''
			result['healed'] = {'sent_to': html}
		if next_random_person and next_random_person['type'] == 'contact':
			context['token'] = request.user.userassociation_set.get(service='facebook').token
		else:
			context['token'] = ''

		result['html'] = render_to_string("send_healing/friends_page.html", context, RequestContext(request))

		return Response(result)
