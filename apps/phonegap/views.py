import json
import facebook
import base64
import imghdr
from cStringIO import StringIO
from datetime import timedelta
from PIL import Image

from django.utils.timezone import datetime
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponseBadRequest, QueryDict

from avatar.models import Avatar
from rest_framework.response import Response
from rest_framework.views import APIView
from oauth_access.access import OAuth20Token, OAuthAccess
from oauth_access.models import UserAssociation

from modality.models import Modality
from modality.forms import ModalityForm
from healers.models import (is_healer, Healer, Appointment, HealerTimeslot,
							Location)
from healers.forms import LocationForm, HealerOptionalInfoForm
from account_hs.views import UserAuthenticated, EmailPasswordAuthentication
from clients.utils import avatar_file_path, get_avatar
from clients.models import ClientLocation, ClientPhoneNumber, Client
from clients.forms import RemoteSessionsForm, AboutClientForm, ShortClientForm
from clients.utils import get_person_content_type
from util import get_name, get_errors
from send_healing.utils import ghp_members, HealingPersonStatus
from send_healing.models import GhpSettings, SentHealing
from phonegap.utils import template_as_string


class IsHealer(UserAuthenticated):
	def get(self, request, format=None):
		return Response(is_healer(request.user) is not None)


class IsAdmin(UserAuthenticated):
	def get(self, request, format=None):
		return Response(request.user.is_superuser)


# for backward compatibility
class Version(APIView):
	def get(self, request, format=None):
		return Response([3, 0, 0])


class UpdateProfile(EmailPasswordAuthentication):
	def post(self, request, format=None):
		form = ShortClientForm(request.POST)

		if not form.is_valid():
			return Response({'errors': get_errors(form)[0]})

		self.get_initial_data()
		self.user.first_name, self.user.last_name = get_name(form.cleaned_data['first_name'])
		self.user.save()
		client = self.user.client
		if form.cleaned_data['about']:
			client.about = form.cleaned_data['about']
			client.save()
		if form.cleaned_data['location']:
			location = Location(
				title=form.cleaned_data['location'],
				address_line1=form.cleaned_data['location'])
			location.google_maps_request(force=True)
			location.save()
			ClientLocation.objects.create(client=client, location=location)

		return Response({'url': request.POST.get('next_url', '')})


class SavePhoto(EmailPasswordAuthentication):
	def post(self, request, format=None):
		self.get_initial_data()
		cropped = json.loads(request.POST.get('cropped', 'false'))
		if cropped:
			error = None
			avatar_file = StringIO(base64.b64decode(request.POST['photo']))
			width, height = Image.open(avatar_file).size
			if width > settings.AVATAR_MAX_WIDTH:
				error = 'The width is more than %s pixels' % settings.AVATAR_MAX_WIDTH
			if height > settings.AVATAR_MAX_HEIGHT:
				error = 'The height is more than %s pixels' % settings.AVATAR_MAX_HEIGHT
			if error is not None:
				return Response(error)
		else:
			avatar_file = request.FILES['file']
		file_type = imghdr.what(avatar_file)
		path = avatar_file_path(self.user, file_type, 'avatar')
		Avatar.objects.filter(user=self.user).delete()
		avatar = Avatar(user=self.user, avatar=path, primary=True)
		avatar.primary = True
		avatar.avatar.storage.save(path, avatar_file)
		avatar.save()
		return Response()


class AddModality(EmailPasswordAuthentication):
	def post(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)

		try:
			data = request.POST['data']
		except:
			return HttpResponseBadRequest()

		form = ModalityForm(QueryDict(data), added_by=healer)
		if form.is_valid():
			form.save()
			return Response()
		else:
			error_list = ''
			error_elements = []
			for error in form.errors:
				error_elements.append('%s' % error)
				if error == '__all__':
					error_list += '%s' % str(form.errors[error])
				else:
					error_list += '%s: %s' % (error, str(form.errors[error]))
			return Response({'error_list': error_list, 'error_elements': error_elements})


class GetAvatarLink(EmailPasswordAuthentication):
	def get(self, request, format=None):
		self.get_initial_data()
		avatar_url = get_avatar(self.user, settings.AVATAR_MAX_WIDTH, True, True)
		return Response({'url': avatar_url})


class GetModalities(EmailPasswordAuthentication):
	def get(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		modalities = list(Modality.objects_approved.get_with_unapproved(healer).filter(healer=healer))
		modalities.reverse()

		return Response({'modalities': render_to_string('healers/settings/specialties_modalities_list.html', {'modalities': modalities}),
						'username': self.user.username, 'max_modalities': settings.MAX_MODALITIES_PER_HEALER,
						'modalities_count': len(modalities)})


class SaveLocation(EmailPasswordAuthentication):
	def post(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		try:
			data = QueryDict(request.POST['data'])
		except:
			return HttpResponseBadRequest()

		def save_location():
			locations_exist = ClientLocation.objects.filter(
				client__user__id=request.user.id, location__is_deleted=False).exists()

			location = location_form.save()
			healer_location = ClientLocation(client=healer, location=location)
			healer_location.save()

			# if this is the first location that the user added, set all timeslots and appts to the new location
			# also mark it as default
			if not locations_exist:
				HealerTimeslot.objects.filter(healer=healer).update(location=location)
				Appointment.all_objects.filter(healer=healer).update(location=location)

				location.is_default = True
				location.save()
			return location

		remote_sessions_form = RemoteSessionsForm(data)

		location_form = LocationForm(data, healer=healer,
			account_setup=True)

		if remote_sessions_form.is_valid():
			healer.remote_sessions = remote_sessions_form.cleaned_data['remote_sessions']
			healer.save()

		if location_form.is_valid() or healer.remote_sessions:
			if location_form.is_valid():
				save_location()
				return Response()

		if not location_form.is_valid():
			if location_form.errors['title'][0] == 'This field is required.':
				location_form.errors['__all__'] = ['You must either set your location OR choose "Yes" for remote sessions']
				location_form.errors.pop('title')

			error_list = ''
			error_elements = []
			for error in location_form.errors:
				error_elements.append('%s' % error)
				if error == '__all__':
					error_list += '%s' % str(location_form.errors[error])
				else:
					error_list += '%s: %s' % (error, str(location_form.errors[error]))
			return Response({'error_list': error_list, 'error_elements': error_elements})


class LocationExists(EmailPasswordAuthentication):
	def get(self, request, format=None):
		self.get_initial_data()
		location_exists = ClientLocation.objects.filter(
				client__user=self.user, location__is_deleted=False).exists()
		return Response(location_exists)


class OptionalInfo(EmailPasswordAuthentication):
	def get(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		phones = ClientPhoneNumber.objects.filter(client=healer)
		return Response({
				'first_name': healer.user.first_name,
				'last_name': healer.user.last_name,
				'phone': (phones[0].number if (len(phones) > 0) else ''),
				'years_in_practice': healer.years_in_practice,
				'website': healer.website,
				'facebook': healer.facebook,
				'twitter': healer.twitter,
				'google_plus': healer.google_plus,
				'linkedin': healer.linkedin,
				'yelp': healer.yelp,
				'ghp_notification_frequency': healer.ghp_notification_frequency,
				})

	def post(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		try:
			data = QueryDict(request.POST['data'])
		except:
			return HttpResponseBadRequest()

		phones = ClientPhoneNumber.objects.filter(client=healer)
		form = HealerOptionalInfoForm(data)
		print form.errors
		if form.is_valid():
			if phones:
				phones[0].number = form.cleaned_data['phone']
				phones[0].save()
			else:
				ClientPhoneNumber.objects.create(client=healer, number=form.cleaned_data['phone'])

			healer.years_in_practice = form.cleaned_data['years_in_practice']
			healer.website = form.cleaned_data['website']
			healer.facebook = form.cleaned_data['facebook']
			healer.twitter = form.cleaned_data['twitter']
			healer.google_plus = form.cleaned_data['google_plus']
			healer.linkedin = form.cleaned_data['linkedin']
			healer.yelp = form.cleaned_data['yelp']
			healer.save()
			return Response()


class WriteABit(EmailPasswordAuthentication):
	def get(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)

		return Response({
			'about': healer.about,
			})

	def post(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		try:
			data = QueryDict(request.POST['data'])
		except:
			return HttpResponseBadRequest()
		form = AboutClientForm(data)
		if form.is_valid():
			healer.about = form.cleaned_data['about']
			healer.save()
			return Response()


class GetListUpdate(APIView):
	def get(self, request, format=None):
		try:
			version = int(request.GET.get('version'))
		except:
			return HttpResponseBadRequest()

		if version == settings.PHONEGAP_LIST_VERSION:
			return Response()
		else:
			return Response({'list_version': settings.PHONEGAP_LIST_VERSION,
				'list_style': template_as_string('list.css'),
				'list_js': template_as_string('list.js'),
				'list_content': template_as_string('list_content.html')})


class GetReceivedHealingList(UserAuthenticated):
	def get(self, request, format=None):
		client_content_type = ContentType.objects.get(app_label='clients', model='client')
		sent_healing = SentHealing.objects.filter(person_content_type=client_content_type, person_object_id=request.user.client.pk)
		now = datetime.now().date()
		received_today = sent_healing.filter(created__range=(now, now + timedelta(days=1))).distinct('sent_by')
		received_yesterday = sent_healing.filter(created__range=(now - timedelta(days=1), now)).distinct('sent_by')
		received_this_week = sent_healing.filter(created__range=(now - timedelta(days=now.weekday()), now - timedelta(days=1))).distinct('sent_by')
		received_this_month = sent_healing.filter(created__range=(now - timedelta(days=now.month), now - timedelta(days=now.weekday()))).distinct('sent_by')
		received_earlier = sent_healing.filter(created__lt=now - timedelta(days=now.month)).distinct('sent_by')

		received = []
		if received_today:
			received.append({'title': 'Today', 'list': received_today})
		if received_yesterday:
			received.append({'title': 'Yesterday', 'list': received_yesterday})
		if received_this_week:
			received.append({'title': 'This Week', 'list': received_this_week})
		if received_this_month:
			received.append({'title': 'This Month', 'list': received_this_month})
		if received_earlier:
			received.append({'title': 'Earlier', 'list': received_earlier})
		return Response(render_to_string('phonegap/received_healing_list.html', {'received': received}))


class GetCircleList(APIView):
	def get(self, request, format=None):
		try:
			page = int(request.GET.get('page'))
			mode = request.GET.get('mode')
		except:
			return HttpResponseBadRequest()

		items_per_page = 10
		if page == 1:
			items_per_page *= 2
		else:
			page += 1
		all_members = ghp_members()
		if request.user.is_authenticated():
			client = request.user.client
			all_members = ghp_members().exclude(pk=client.pk)

		if mode == 'favorites':
			client_content_type = get_person_content_type('client')
			favorite_ids = HealingPersonStatus.objects.filter(client=client, status=HealingPersonStatus.FAVORITE,
						person_content_type=client_content_type).values_list('person_object_id', flat=True)
			all_members = all_members.filter(id__in=favorite_ids)
		elif mode == 'urgent':
			urgent_ids = GhpSettings.objects.filter(urgent=True).values_list('user', flat=True)
			all_members = all_members.filter(user__in=urgent_ids)
		elif mode == 'facebook':
			try:
				fb_id = request.user.userassociation_set.get(service='facebook').identifier[3:]
				facebook_key = settings.OAUTH_ACCESS_SETTINGS['facebook']['keys']
				token = facebook.get_app_access_token(facebook_key['KEY'], facebook_key['SECRET'])
			except UserAssociation.DoesNotExist:
				token = ''
			if token:
				graph = facebook.GraphAPI(token)
				friends = graph.get_connections(id=fb_id, connection_name='friends')['data']
				friends = ['fb-' + friend['id'] for friend in friends]
				users = UserAssociation.objects.filter(identifier__in=friends).values_list('user_id', flat=True)
				all_members = Client.objects.filter(user__in=users)
			else:
				return Response(render_to_string('phonegap/link_with_facebook.html'))

		members = all_members[(page - 1) * items_per_page:page * items_per_page]
		is_last_page = all_members.count() < items_per_page * page

		return Response(render_to_string('phonegap/list_contents.html', {'members': members,
			'next_page': page + 1,
			'is_last_page': is_last_page,
			'mode': mode}))


class FacebookAssociateUser(UserAuthenticated):
	def post(self, request, format=None):
		try:
			token = request.POST.get('token')
		except:
			return HttpResponseBadRequest()

		access = OAuthAccess('facebook')
		auth_token = OAuth20Token(token)
		user, error = access.callback(request, access, auth_token, is_ajax=True)
		if user:
			return Response()
		else:
			return Response(error)
