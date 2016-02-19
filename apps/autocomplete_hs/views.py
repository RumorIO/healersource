# -*- coding: utf-8 -*-

import json
from itertools import chain

from django.db.models import Sum, Max, Min
from django.db.models.query_utils import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import (HttpResponse, HttpResponseForbidden,
						HttpResponseBadRequest, Http404)
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from account_hs.views import UserAuthenticated, EmailPasswordAuthentication
from util import get_name
from contacts_hs.models import ContactInfo, ContactPhone
from clients.models import Client
from clients.utils import get_avatar
from friends.models import Friendship, Contact
from geonames.models import GeoName
from modality.models import Modality, ModalityCategory
from healers.models import Healer, Zipcode, is_wellness_center, is_healer
from healers.forms import ClientsSearchForm
from healers.views import HealerAuthenticated


def get_providers(q, limit, get_all=False):
	qs = Healer.objects.all()
	if not get_all:
		qs = qs.exclude(profileVisibility=Healer.VISIBLE_CLIENTS)

	return ClientsSearchForm.search_by_name_or_email(qs, q, get_all)[:limit]


def autocomplete_friends_first_or_last(request):
	"""
	Provides username matching based on matches of the beginning of the
	usernames of friends.
	"""
	if not request.user.is_authenticated():
		response = HttpResponseForbidden()

	else:
		q = request.GET.get("term")

		if not q:
			return HttpResponse(json.dumps(''))

		friends = Friendship.objects.friends_for_user(request.user)

		content = []
		for friendship in friends:
			friend_user = friendship["friend"]
			if friend_user.first_name.lower().startswith(q) or friend_user.last_name.lower().startswith(q):
				try:
					profile = friend_user.client
					entry = {
						"id": friend_user.username,
						"label": '%s&nbsp;%s<div class="clearfix"></div>' % (get_avatar(friend_user, 50), unicode(profile)),
						"value": unicode(profile)
					}

					if not entry in content:
						content.append(entry)

				except ObjectDoesNotExist:
					pass

		response = HttpResponse(json.dumps(content))

	setattr(response, "djangologging.suppress_output", True)
	return response


def all_clients(user):
	"""
	Returns all friends list and clients qs for user
	"""
	friends = Friendship.objects.friends_for_user(user.id)
	friend_users = [f["friend"] for f in friends]
	if is_wellness_center(user):
		friend_users.append(user)
	clients = Client.objects.select_related('user')\
		.filter(user__in=friend_users)
	return clients, friend_users


def build_client_entry(client):
	to_email = client.user.email
	if not to_email:
		#try getting email from ContactInfo
		from contacts_hs.models import ContactEmail
		to_email = ContactEmail.objects.get_first_email(client.user)

	label = '%s&nbsp;%s<div class="clearfix"></div>'
	return {
		"id": client.id,
		"label": label % (get_avatar(client.user, 40, external=True), unicode(client)),
		"value": unicode(client),
		"type": "client",
		'has_email': 1 if to_email else 0
	}


def autocomplete_all_clients(request):
	"""Provide all clients of user for jquery autocomplete in json format."""
	user = request.user
	clients = all_clients(user)[0]
	healer = is_healer(user)
	if healer:
		centers = healer.get_wellness_centers().filter(clients_visible_to_providers=True)
		if centers.exists():
			for center in centers:
				clients |= all_clients(center.user)[0]
	content = []
	for client in clients:
		entry = build_client_entry(client)

		if not entry in content:
			content.append(entry)

	return json.dumps(content)


def autocomplete_providers(request):
	q = request.GET.get("term")

	healers = Healer.complete.all()
	if q:
		healers = healers.filter(Q(user__first_name__istartswith=q) | Q(user__last_name__istartswith=q))

	label = '%s&nbsp;%s<div class="clearfix"></div>'
	content = [{
		"id": healer.pk,
		"label": label % (get_avatar(healer.user, 40), unicode(healer)),
		"value": unicode(healer),
	} for healer in healers]

	return HttpResponse(json.dumps(content))


def autocomplete_client_first_or_last(request):
	"""
	Provides username matching based on matches of the beginning of the
	usernames of friends.
	"""
	if not request.user.is_authenticated():
		response = HttpResponseForbidden()

	else:
		q = request.GET.get("term", '').lower()

		if not q:
			return HttpResponse(json.dumps(''))

		clients, friend_users = all_clients(request.user)

		content = []
		for client in clients:
			friend_user = client.user
			if (friend_user.first_name.lower().startswith(q) or
				friend_user.last_name.lower().startswith(q)):

				entry = build_client_entry(client)

				if not entry in content:
					content.append(entry)

		emails = (u.email.lower() for u in friend_users if u.email)
		contacts = Contact.objects.exclude(email__in=emails)\
					.exclude(users__in=friend_users)\
					.filter(user=request.user, name__icontains=q)\
					.order_by('-email')[:10]

		build_contacts_entries(contacts, [], content, q)
		content.append(get_import_contacts_content(True))

		response = HttpResponse(json.dumps(content))

	setattr(response, "djangologging.suppress_output", True)
	return response


def autocomplete_search_name_or_email(request, show_add_friend_links=False,
										return_username=False,
										delete_account=False):
	add = request.GET.get("add", False)
	q = request.GET.get("term")

	if delete_account and not request.user.is_superuser:
		raise Http404

	if not q:
		return HttpResponse(json.dumps(''))

	limit = int(request.GET.get("limit", 10))
	healers = get_providers(q, limit, delete_account)

	content = []
	for healer in healers:
		user = healer.user
		try:
			profile = user.client
			provider_name = unicode(profile)

			if show_add_friend_links:
				entry = {
					"id": healer.healer_profile_url(),

					"label": "<table class='search_provider_add_friend_row'><tr><td>%s</td>" \
						         "<td style='padding-left:6px;'>%s" \
						         "<div class='icon_users_add'><a href='%s' class='ac_inline'>Add to My Clients</a></div>" \
						         "<div class='icon_recommend'><a href='%s' class='ac_inline'>Add Referral</a></div>" \
						      "</div>" \
						      "</td></tr></table>" %
					         (get_avatar(user, 50),
					          provider_name,
					          reverse("friend_add", kwargs={'friend_type':'clients', 'user_id':user.id}),
					          reverse("friend_add", kwargs={'friend_type':'referrals', 'user_id':user.id}) ),
					"value": provider_name,
					"action": ""
				}
			else:
				if add:
					action = reverse("friend_add", kwargs={'friend_type':'referrals', 'user_id':user.id})
				else:
					action = healer.healer_profile_url() if not return_username else user.username,
				entry = {
					"id": action,
					"label": '%s&nbsp;%s<div class="clearfix"></div>' % (get_avatar(user, 50), provider_name),
					"value": provider_name,
					"action": "add" if add else ""
				}
				if delete_account:
					entry['username'] = user.username
					if healer.is_deleted:
						status = 'deleted'
					elif user.is_active:
						status = 'active'
					else:
						status = 'inactive'
					entry['status'] = status

			content.append(entry)
		except ObjectDoesNotExist:
			pass

	response = HttpResponse(json.dumps(content))

	setattr(response, "djangologging.suppress_output", True)
	return response


class AutocompleteModality(EmailPasswordAuthentication):
	"""
	Returns list of modalities
	"""
	def get(self, request, format=None):
		self.get_initial_data()
		healer = get_object_or_404(Healer, user=self.user)
		try:
			q = request.GET.get('term')
		except:
			return HttpResponseBadRequest()

		modalities = Modality.objects_approved.filter(visible=True).filter(title__istartswith=q)[
					 :settings.NUMBER_OF_MODALITIES_IN_AUTOCOMPLETE]

		if len(modalities) < settings.NUMBER_OF_MODALITIES_IN_AUTOCOMPLETE:
			modalities = list(chain(modalities,
				Modality.objects_approved.get_with_unapproved(healer).filter(visible=True).filter(title__icontains=q).exclude(title__istartswith=q)[
				:settings.NUMBER_OF_MODALITIES_IN_AUTOCOMPLETE - len(modalities)]))

		content = [{
			"id": m.id,
			"label": m.title,
			"value": m.title
		} for m in modalities]

		content.append({"id":0, "label": "<span class='add_specialty_link'>"
		                                 "Create a New Specialty &raquo;</span>", "value": q})

		return Response(content)


def autocomplete_modality_or_category(request):
	"""
	Returns list of categories and modalities
	"""
	q = request.GET.get("term")

	if not q:
		return HttpResponse(json.dumps(''))

	try:
		limit = int(request.GET.get("limit", 0))
	except ValueError:
		limit = 0
	if not limit:
		limit = settings.NUMBER_OF_MODALITIES_IN_AUTOCOMPLETE

	categories = ModalityCategory.objects.filter(title__istartswith=q)[:4]

	category_list = [{
		"id": c.id,
		"label": "> Search for all types of " + c.title,
		"value": c.title,
		"is_category": 1
	} for c in categories]

	modalities = Modality.objects_approved.filter(visible=True).filter(title__istartswith=q)[
				 :limit - len(category_list)]

	if len(modalities) < (limit - len(category_list)):
		modalities = list(chain(modalities,
			Modality.objects_approved.filter(visible=True).filter(title__icontains=q).exclude(title__istartswith=q)[
			:limit - len(modalities) - len(category_list)]))

	modality_list = [{
		"id": m.id,
		"label": m.title,
		"value": m.title,
		"is_category": 0
	} for m in modalities]

	response = HttpResponse(json.dumps(category_list + modality_list))
	return response


def get_import_contacts_content(attendees_request=False):
	img_facebook = '<img src="%shealersource/img/icons/social/facebook.png"/>' % settings.STATIC_URL
	img_google = '<img src="%shealersource/img/icons/social/google.png"/>' % settings.STATIC_URL
	element = {'id': '', 'value': ''}
	if attendees_request:
		float_box_extension = ''
	else:
		float_box_extension = '?fb=1'

	html_content = ('<a href="%s%s" class="import_contacts_entry">Import Contacts: %s %s</a>' %
		(reverse('import_contacts_status'), float_box_extension, img_google, img_facebook))
	if attendees_request:
		element['label'] = html_content
	else:
		element['value'] = html_content

	return element


def build_contacts_entries(contacts, providers, content, q, with_info=False, with_email=False):
	info = {}
	if with_info:
		info_qs = ContactInfo.objects.filter(contact__in=contacts)
		info = dict((i.contact_id, i) for i in info_qs)

		phones_qs = ContactPhone.objects.filter(contact__in=info_qs)
		phones = {}
		for p in phones_qs:
			phones.setdefault(p.contact_id, []).append(p.number)

	for provider in providers:
		user = provider.user
		try:
			provider_name = unicode(user.client)

			entry = {
				"id": provider.id,
				"label": '%s&nbsp;%s<div class="clearfix"></div>' % (get_avatar(user, 50), provider_name),
				"value": provider_name,
				"type": "provider"
			}

			entry['email'] = user.email
			entry['has_email'] = 1

			content.append(entry)
		except ObjectDoesNotExist:
			pass

	for contact in contacts:
		entry = {
			"id": contact.id,
			"value": contact.name,
			"type": "contact"
		}

		contact_info = info.get(contact.id, None)
		if contact_info:
			entry['first_name'] = contact_info.first_name
			entry['last_name'] = contact_info.last_name

			phone = phones.get(contact_info.id, None)
			if phone:
				entry['phone'] = phone[0]
		else:
			entry['first_name'], entry['last_name'] = get_name(contact.name)

		label_text = contact.name
		label_class = "google_icon"

		if contact.email:
			entry['email'] = contact.email
			entry['has_email'] = 1

			if "@" in q:
				label_text = contact.email

		else:
			entry['has_email'] = 0

			try:
				entry['facebook_id'] = contact.contactsocialid_set\
					.filter(service="facebook")[0].social_id
				label_class = "facebook_icon"

			except IndexError:
				pass

		if with_email and 'email' in entry:
			label_text += ' - ' + entry['email']
		label = '<div class="%s">%s<div class="clearfix"></div></nobr>'
		entry["label"] = label % (label_class, label_text)

		if not entry in content:
			content.append(entry)


class AutocompleteClientsWithNotes(HealerAuthenticated):
	def get(self, request, format=None):
		self.get_initial_data()
		try:
			q = request.GET.get('term')
		except:
			return HttpResponseBadRequest()

		clients_with_notes_ids = list(set(self.healer.notes.all().values_list('client', flat='True')))
		clients = Client.objects.filter(pk__in=clients_with_notes_ids)
		if q:
			clients = clients.filter(Q(user__first_name__istartswith=q) | Q(user__last_name__istartswith=q))

		content = []
		for client in clients:
			entry = build_client_entry(client)

			if not entry in content:
				content.append(entry)

		return Response(content)


class AutocompleteContacts(UserAuthenticated):
	def get(self, request, format=None):
		q = request.GET.get('term').lower()
		limit = int(request.GET.get('limit', 10))
		if limit <= 0 or limit > 10:
			limit = 10

		if not q:
			return Response()

		contacts = Contact.objects.filter(user=request.user)
		if '@' in q:
			contacts = contacts.filter(email__icontains=q)
		else:
			contacts = contacts.filter(name__icontains=q)
		contacts = contacts.order_by('-email')[:limit]

		providers = []
		if request.GET.get('with_providers', False):
			providers = get_providers(q, limit / 2)  # row with provider higher two times
			limit = limit - len(providers) * 2

		content = []
		if request.GET.get('show_term', False):
			content.append({
				'id': q,
				'value': q,
				'type': 'email'
			})

		with_info = request.GET.get('contact_info', False)
		build_contacts_entries(contacts, providers, content, q, with_info, with_email=True)

		if request.GET.get('import_link', False):
			content.append(get_import_contacts_content())

		return Response(content)


class AutocompleteCity(APIView):
	def get(self, request, format=None):
		"""
		Returns max 7 zipcodes for autocomplete by city name
		If input digital returns empty results
		"""
		q = request.GET.get('term')
		any_location = request.GET.get('any_location', False)

		if not q or q.isdigit():
			return Response()

		zipcodes = (Zipcode.objects
			.values('city', 'state')
			.annotate(sum_pop=Sum('population'), max_id=Max('id'), code=Min('code'))
			.filter(city__istartswith=q)
			.order_by('-sum_pop')[:7])

		result = [{
			'id': zipcode['max_id'],
			'label': '%s, %s' % (zipcode['city'].title(), zipcode['state']),
			'value': '%s, %s' % (zipcode['city'].title(), zipcode['state']),
			'city': zipcode['city'].title(),
			'state': zipcode['state'],
			'zipcode': zipcode['code']
		} for zipcode in zipcodes]

		if any_location:
			result += [{
				'id': 0,
				'label': '<div style="border-top: 1px solid grey;">» <em>Search Everywhere</em></div>',
				'value': 'Everywhere',
				'city': '',
				'state': '',
				'zipcode': ''
			}]

			result += [{
				'id': 0,
				'label': '<div style="border-top: 1px solid grey;">» <em>Search for Phone, Online, Skype, or Distance Sessions</em></div>',
				'value': 'Phone, Online, Skype, or Distance Sessions',
				'city': '',
				'state': '',
				'zipcode': ''
			}]

		return Response(result)


class AutocompleteGeoName(APIView):
	def get(self, request, format=None):
		"""
		Returns max 7 geonames for autocomplete by name
		"""
		q = request.GET.get('term')

		if not q or q.isdigit():
			return Response()

		geonames = (GeoName.objects
			.filter(name__istartswith=q)
			.order_by('-population')[:7])

		result = [{
			'label': geoname.short_name,
			'value': geoname.id
		} for geoname in geonames]

		return Response(result)
