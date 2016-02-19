import json
import re
from bs4 import BeautifulSoup
from bs4.dammit import UnicodeDammit
from html5lib import HTMLParser, sanitizer, getTreeWalker, serializer
from datetime import date

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.functional import allow_lazy
from django.utils.encoding import force_unicode
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template import loader
from django.template.context import Context
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, EmailMessage

from django_yubin import queue_email_message
from django_yubin.constants import PRIORITIES
from friends.models import Contact

from contacts_hs.models import ContactEmail, ContactSocialId
from healers.models import (ClientInvitation, Clients, Referrals, Healer,
							ReferralInvitation, is_my_client, is_healer,
							is_wellness_center, Appointment, Room,
							WellnessCenterTreatmentType, TreatmentTypeLength,
							HealerTimeslot, WellnessCenter,
							WellnessCenterTreatmentTypeLength)
from modality.models import Modality
from util import absolute_url
import clients


class Setup_Step_Names():
	provider_steps = (
		'1: Set Your Location',
		'2: Enter Your Specialties',
		'3: Optional Information',
		'4: Upload Your Photo',
		'5: Write a Bit About Yourself',
		'6: Accept Payments Online',
		'7: Setup Your Referral Network',
		'8: Import Your Blog',
		'9: Import Your Contacts',
		'10: Setup Your Schedule',
		'11: Add Treatment Types',
		'12: Edit Schedule Settings',
		'13: Set Your Availability'
	)

	wellness_center_steps = (
		'1: Set Your Center\'s Location',
		'2: Enter the Specialties at Your Center',
		'3: Optional Information',
		'4: Upload Your Photo',
		'5: Write a Bit About Your Center',
		'6: Add Providers',
		'7: Accept Payments Online',
		'8: Import Your Blog',
		'9: Import Your Contacts',
		'10: Setup Your Schedule',
		'11: Add Treatment Types',
		'12: Edit Schedule Settings',
		'13: Set Your Availability'
	)

	@classmethod
	def get_steps(cls, healer):
		if is_wellness_center(healer):
			return cls.wellness_center_steps
		else:
			return cls.provider_steps


def get_friend_classes(friend_type):
	if friend_type == 'referrals':
		FriendClass=Referrals
		InvitationClass=ReferralInvitation

	elif friend_type == "clients" or friend_type == "healers":
		FriendClass=Clients
		InvitationClass=ClientInvitation

	else:
		FriendClass=None
		InvitationClass=None

	return FriendClass, InvitationClass

### You MUST set request.friend_type in order to use this processor
def friend_processor(request):
	if request.friend_type == 'referrals':
		page_title = "Referrals"
		requested_text = "to Refer To you"

	elif request.friend_type == "clients":
		page_title = "Client"
		requested_text = "to be your Client"

	elif request.friend_type == "healers":
		page_title = "Provider"
		requested_text = "to be your Provider"

	else:
		page_title = "Something is Wrong. You must set request.friend_type"
		requested_text = "Something is Wrong. You must set request.friend_type"

	return {
		"page_title":page_title,
		"requested_text":requested_text,
		"friend_type":request.friend_type
	}

### You MUST set request.friend_type and request.other_user in order to use this processor
def friend_bar_processor(request):
	if not request.friend_type:
		return {"other_user": request.other_user}

	context = friend_processor(request)
	other_user = request.other_user

	FriendClass, InvitationClass = get_friend_classes(request.friend_type)

	is_me = False
	is_client = False
	if request.user.is_authenticated():

		if request.friend_type == 'referrals':
			context['referal_to'] = Referrals.objects.refers_to(request.user, other_user)
			context['referal_from'] = Referrals.objects.refers_to(other_user, request.user)
			is_client = context['referal_to'] or is_my_client(request.user, other_user)

		else:
			is_client = is_my_client(other_user, request.user)

			previous_invitation_to = None
			if not is_client:
				previous_invitations_to = InvitationClass.objects.filter(
					to_user=other_user, from_user=request.user, status="2")
				if previous_invitations_to:
					previous_invitation_to = previous_invitations_to[0]

			context["previous_invitation_to"] = previous_invitation_to

		if request.user == other_user:
			is_me = True
		else:
			is_me = False

		#	previous_invitation_from = None
		#	previous_invitations_from = InvitationClass.objects.invitations(to_user=request.user, from_user=other_user, status="2")
		#	if previous_invitations_from:
		#		previous_invitation_from = previous_invitations_from[0].from_user

	context["is_me"] = is_me
	context["is_client"] = is_client
	context["other_user"] = other_user
	#	context["previous_invitation_from"] =  previous_invitation_from

	return context


def get_healer_info_context(healer, request):
	client = None
	client_id = ""
	request.friend_type = None
	is_profile_visible = True
	is_client = False
	try:
		client = clients.models.Client.objects.get(user__id=request.user.id)
		request.friend_type = 'referrals' if is_healer(client) else "healers"
		client_id = client.id
		is_client = is_my_client(healer.user, request.user)
	except ObjectDoesNotExist:
		pass

	is_profile_visible = healer.is_visible_to(request.user, is_client)

	if not is_profile_visible and not request.user.is_superuser:
		if request.user != healer.user:
			return is_client, False, {}

	locations = healer.get_locations(user=request.user, is_client=is_client,
		skip_center_locations=True)

	#	referring_users = [o['friend'] for o in Referrals.objects.referrals_to(healer.user)]
	#	healers = Healer.objects.filter(user__in=referring_users)
	#	referrals_to_me = [h.user for h in healers if h.is_visible_to(request.user)]
	referrals_to_me_count = Referrals.objects.referrals_to(healer.user, count=True)

	phones = clients.models.ClientPhoneNumber.objects.filter(client=healer)

	if request.user == healer.user:
		modalities = Modality.objects_approved.get_with_unapproved(healer=healer)
	else:
		modalities = Modality.objects_approved
	modalities = list(modalities.filter(healer=healer, visible=True))
	modalities.reverse()

	request.other_user = healer.user

	return is_client, True, {
		"healer": healer,
		"client": client,
		"client_id": client_id,
		"is_my_client": is_client,
		"locations": locations,
		"referrals_to_me_count": referrals_to_me_count,
		"phone": (phones[0].number if (len(phones) > 0) else ''),
		"modalities": modalities,
		"is_schedule_visible": healer.is_schedule_visible(request.user, is_client),
		"review_exist": healer.reviews.filter(reviewer__user=request.user).count() if request.user.is_authenticated() else False,
		"is_review_permission": healer.is_review_permission(request.user, is_client),
		}


def invite_or_create_client_friendship(client_user, healer_user, send_client_request_email=False):
	#if the person is in my contacts list > auto add them, otherwise require a confirmation

	is_client = is_my_client(healer_user=healer_user, client_user=client_user)

	if is_client:
		return

	healer = is_healer(healer_user)
	if not healer:
		raise Healer.DoesNotExist

	contact = ContactEmail.objects.filter(email=client_user.email, contact__healer=healer).count()

	if healer.client_screening == Healer.SCREEN_ALL or \
		(healer.client_screening == Healer.SCREEN_NOT_CONTACTS and not contact):

		invitation_to = ClientInvitation.objects.filter(from_user=client_user, to_user=healer_user, status="2")

		if not invitation_to:
			invitation = ClientInvitation(from_user=client_user, to_user=healer_user, message="", status="2")
			invitation.save()

		if send_client_request_email:
			ctx = {
				"client_name": str(client_user.client),
				"accept_url": get_full_url('friend_accept', args=['clients', client_user.id]),
				"decline_url": get_full_url('friend_decline', args=['clients', client_user.id])
			}

			subject = render_to_string("friends/client_request_subject.txt", ctx)
			send_hs_mail(subject, "friends/client_request_message.txt", ctx, settings.DEFAULT_FROM_EMAIL, [healer_user.email])

	elif healer.client_screening == Healer.SCREEN_NONE or \
	     (healer.client_screening == Healer.SCREEN_NOT_CONTACTS and contact):

		Clients.objects.create(from_user=healer_user, to_user=client_user)

	else:
		raise Exception

def get_full_url(view_name, args=None):
	return absolute_url(reverse(view_name, args=args))


def send_html_mail(subject, message, message_html, from_email, recipient_list,
				   priority="normal", fail_silently=False, auth_user=None,
				   auth_password=None, bcc=None, reply_to=None, attachment_path=None):
	"""
	Function to queue HTML e-mails
	"""
	if reply_to is None:
		reply_to = settings.REPLY_TO

	priority = PRIORITIES[priority]

	# need to do this in case subject used lazy version of ugettext
	subject = force_unicode(subject)
	message = force_unicode(message)

	email = EmailMultiAlternatives(
		subject,
		message,
		from_email,
		recipient_list,
		bcc=bcc,
		headers={'Reply-To': reply_to})
	email.attach_alternative(message_html, "text/html")
	if attachment_path is not None:
		# email.attach(attachment_filename, attachment_content)
		email.attach_file(attachment_path)

	queue_email_message(email, priority=priority)
	return 1


def send_queued_mail(subject, message, from_email, recipient_list, bcc=None, fail_silently=False, reply_to=None):
	"""
	Function to queue HTML e-mails
	"""

	priority = PRIORITIES['normal']

	# need to do this in case subject used lazy version of ugettext
	subject = force_unicode(subject)
	message = force_unicode(message)

	def send_email():
		email = EmailMultiAlternatives(
			subject,
			message,
			from_email,
			recipient_list,
			bcc=bcc,
			headers={'Reply-To': (reply_to if reply_to else settings.REPLY_TO)})
		queue_email_message(email, priority=priority)

	if fail_silently:
		try:
			send_email()
		except:
			pass
	else:
		send_email()
	return 1


def send_regular_mail(subject, message, from_email, recipient_list, bcc=None, fail_silently=False, reply_to=None):
	if reply_to is None:
		reply_to = settings.REPLY_TO

	email = EmailMessage(subject=subject,
						body=message,
						from_email=from_email,
						to=recipient_list,
						bcc=bcc,
						headers={'Reply-To': reply_to})
	email.send(fail_silently=fail_silently)


def send_hs_mail(subject, template_name, ctx, from_email, recipient_list,
					fail_silently=False, auth_user=None, auth_password=None,
					html_template_name=None, bcc=None,
					attachment_path=None):

	t = loader.get_template(template_name)
	message = t.render(Context(ctx))

#	for n in t.nodelist:
#		if hasattr(n, 's'):
#			n.s = n.s.replace('\n', '<br />')
#
#			pass

	if settings.EMAIL_DEBUG:
		send_regular_mail(subject, message, from_email, recipient_list,
			fail_silently=fail_silently)

	else:
		ctx['html_email'] = True
		if html_template_name:
			message_html = render_to_string(html_template_name, ctx)
		else:
			body_html = t.render(Context(ctx))
			body_html = body_html.replace('\n', '<br />')
			ctx['body'] = body_html
			message_html = render_to_string("email_html_base.html", ctx)

	#	message_html = render_to_string(template_name, ctx)

		send_html_mail(subject, message, message_html, from_email, recipient_list,
			fail_silently=fail_silently, auth_user=auth_user,
			auth_password=auth_password, bcc=bcc,
			attachment_path=attachment_path)


#	subject, from_email, to = 'hello', 'from@example.com', 'to@example.com'
#	text_content = 'This is an important message.'
#	html_content = '<p>This is an <strong>important</strong> message.</p>'
#	msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
#	msg.attach_alternative(html_content, "text/html")
#	msg.send()

def get_imported_contacts(user, clients_users, referrals_from_me):
	invitations_qs = ClientInvitation.objects.filter(to_user=user).filter(status="2")
	invitations = [invitation.from_user for invitation in invitations_qs]

	exclude_emails = [u.email.lower() for u in invitations]
	exclude_emails += [cu.email.lower() for cu in clients_users if cu.email]
	exclude_emails += [r.email.lower() for r in referrals_from_me if r.email]
	#
	#	invitations_from_me = JoinInvitation.objects.filter(from_user=request.user).exclude(status="1")
	#	exclude_emails += [i.from_user.email.lower() for i in invitations_from_me]

	contacts_list = Contact.objects.filter(user=user).exclude(email__in=exclude_emails).order_by('name')
	contacts_dict = dict([(c.id, c) for c in contacts_list])
	facebook_ids = ContactSocialId.objects.filter(contact__in=contacts_list, service="facebook")
	for fb_id in facebook_ids:
		contact = contacts_dict.get(fb_id.contact_id, None)
		if contact:
			contact.facebook_id = fb_id.social_id
		#		for invite in invitations_from_user:
		#			contact = contacts_dict.get(invite.contact.id, None)
		#			if contact:
		#				contact.invited = True

	return invitations, contacts_list

def html_sanitize(text):
	if not text:
		return ''
	p = HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
	element = p.parseFragment(text)
	walker = getTreeWalker("etree")
	stream = walker(element)
	s = serializer.HTMLSerializer()
	text = s.render(stream)
	text = UnicodeDammit(text, ["utf-8"])
	REMOVE_ATTRIBUTES = [
		'lang','language','onmouseover','onmouseout','script','font','style',
		'dir','face','size','color','style','class','width','height','hspace',
		'border','valign','align','background','bgcolor','text','link','vlink',
		'alink','cellpadding','cellspacing', 'id']

	soup = BeautifulSoup(text.unicode_markup)
	for attribute in REMOVE_ATTRIBUTES:
		for tag in soup.findAll():

			if(attribute == 'style'):
				new_style = ''
				style = tag.attrs.get('style', None)
				if style:
					if style.find('normal') != -1: new_style += " font-weight:normal; "
					elif style.find('bold') != -1: new_style += " font-weight:bold; "
					if style.find('italic') != -1: new_style += " font-style: italic; "
					if style.find('underline') != -1: new_style += " text-decoration: underline; "
					tag.attrs['style'] = new_style

			else:
				del(tag[attribute])

	html = soup.prettify('utf-8')
	try:
		body = re.findall(r'<body>(.*)</body>', html, re.S)[0].strip()
	except IndexError:
		body = html
	return body

def truncate_html_words(s, num, end_text='...'):
	"""Truncates HTML to a certain number of words (not counting tags and
	comments). Closes opened tags if they were correctly closed in the given
	html. Takes an optional argument of what should be used to notify that the
	string has been truncated, defaulting to ellipsis (...).

	Newlines in the HTML are preserved.
	"""
	s = force_unicode(s)
	length = int(num)
	if length <= 0:
		return u''
	html4_singlets = ('br', 'col', 'link', 'base', 'img', 'param', 'area', 'hr', 'input')
	# Set up regular expressions
	re_words = re.compile(r'&.*?;|<.*?>|(\w[\w-]*)', re.U)
	re_tag = re.compile(r'<(/)?([^ ]+?)(?:(\s*/)| .*?)?>')
	# Count non-HTML words and keep note of open tags
	pos = 0
	end_text_pos = 0
	words = 0
	open_tags = []
	while words <= length:
		m = re_words.search(s, pos)
		if not m:
			# Checked through whole string
			break
		pos = m.end(0)
		if m.group(1):
			# It's an actual non-HTML word
			words += 1
			if words == length:
				end_text_pos = pos
			continue
		# Check for tag
		tag = re_tag.match(m.group(0))
		if not tag or end_text_pos:
			# Don't worry about non tags or tags after our truncate point
			continue
		closing_tag, tagname, self_closing = tag.groups()
		tagname = tagname.lower()  # Element names are always case-insensitive
		if self_closing or tagname in html4_singlets:
			pass
		elif closing_tag:
			# Check for match in open tags list
			try:
				i = open_tags.index(tagname)
			except ValueError:
				pass
			else:
				# SGML: An end tag closes, back to the matching start tag, all unclosed intervening start tags with omitted end tags
				open_tags = open_tags[i+1:]
		else:
			# Add it to the start of the open tags list
			open_tags.insert(0, tagname)
	if words <= length:
		# Don't try to close tags if we don't need to truncate
		return s
	out = s[:end_text_pos]
	if end_text:
		out += ' ' + end_text
	# Close any tags still open
	for tag in open_tags:
		out += '</%s>' % tag
	# Return string
	return out
truncate_html_words = allow_lazy(truncate_html_words, unicode)

def get_fill_warning_links(healer, modalities=None, wcenter=None, editing_self=True):
	fill_warning_links = {}

	if wcenter:
		if editing_self:
			avatar_text = "set your center's photo"
			about_text = "write something about your center"
			modalities_text = "add your center's specialties"
		else:
			avatar_text = "set this provider's photo"
			about_text = "write something about this provider"
			modalities_text = "add this provider's specialties"

	else:
		avatar_text = "set your photo"
		about_text = "write something about yourself"
		modalities_text = "add your specialties"

	if not healer.remote_sessions:
		if not healer.get_locations():
			fill_warning_links['location'] = {
				'href': reverse('provider_setup', args=[1]), 'text': 'Add a Location or Set Remote Sessions to "Yes"'}
	if not healer.user.avatar_set.count():
		fill_warning_links['avatar'] = {'href': reverse('avatar_change'), 'text': avatar_text}

	if healer.about == "":
		fill_warning_links['about'] = {'href': reverse('healer_edit'), 'text': about_text,
										'attrs': 'onclick="return addRedBorder(\'.te\');"'}

	if not modalities:
		if not healer.has_specialities():
			fill_warning_links['specialties'] = {'href': reverse('provider_setup', args=[2]), 'text': modalities_text}

	return fill_warning_links


def get_visible_healers_in_wcenter(user, wellness_center):
	healers = wellness_center.get_healers_in_wcenter()
	healers_visible = [h for h in healers if h.is_visible_to(user)]
	for h in healers_visible:
		h.show_schedule = h.is_schedule_visible(user)
	return healers_visible


def get_wcenter_location_ids(user):
	return clients.models.ClientLocation.objects.filter(client__user=user, location__is_deleted=False).values_list('location', flat=True)


def get_healer_wcenters_locations(healer):
	locations_all = []
	for wcenter in healer.get_wellness_centers():
		locations_all += get_wcenter_location_ids(wcenter.user)
	return locations_all


def get_wcenter_unconfirmed_appts(wcenter, healer=None):
	if healer is not None:
		appts = Appointment.objects.get_active(healer)
	else:
		appts = Appointment.objects.get_active(wcenter.healer, wcenter.get_healers_in_wcenter())
	return appts.filter(location__in=get_wcenter_location_ids(wcenter.user), confirmed=False)


def get_healers_in_wcenter_with_schedule_editing_perm(healer, order_by_id=False):
	try:
		wcenter = healer.wellnesscenter
	except:
		return

	healers = wcenter.get_healers_in_wcenter().values_list('pk', flat=True)
	healers = Healer.objects.filter(pk__in=healers,
								wellness_center_permissions=wcenter)
	if order_by_id:
		healers = healers.order_by('id')
	else:
		healers = healers.order_by('user__first_name')
	return healers


def get_healer(requesting_user, requested_username):
	healer = get_object_or_404(Healer, user=requesting_user)
	healer_requesting = healer

	if (is_wellness_center(requesting_user) and
			requesting_user.username != requested_username):
		healer = get_object_or_404(Healer, user__username=requested_username)
		if (healer not in
				get_healers_in_wcenter_with_schedule_editing_perm(healer_requesting)):
			raise Http404
	return healer


def check_center_permissions(center_user, healer_user):
	if center_user != healer_user:
		get_healer(center_user, healer_user.username)


def check_room(room_id, location_id, treatment_length):
	# check if location has any rooms and if so, force room selection
	if Room.objects.filter(location=location_id).exists():
		try:
			room = Room.objects.get(id=room_id)
			if room.location_id != location_id:
				raise Exception('Invalid room for that location.')
			if treatment_length:
				rooms = treatment_length.treatment_type.rooms.all()
				if rooms and room not in rooms:
					raise Exception('Invalid room for that treatment type.')
		except Room.DoesNotExist:
			raise Exception('Could not find that room.')

		return room


def wcenter_healer_has_treatment_types_(requesting_user, healer):
	wellnesscenter = is_wellnesscenter = is_wellness_center(requesting_user)
	if is_wellnesscenter and healer.user != requesting_user:
		try:
			return healer.wellness_center_treatment_types.get(
				wellness_center=wellnesscenter).treatment_types.exists()
		except WellnessCenterTreatmentType.DoesNotExist:
			pass
	return False


def exclude_not_selected_treatment_lengths(tlengths, wcenter, provider):
		wttl = WellnessCenterTreatmentTypeLength.objects.filter(
			wellness_center=wcenter, healer=provider)
		if wttl.exists():
			wttl = wttl[0]
			selected_ttls = wttl.treatment_type_lengths.all()
			treatment_types_to_exclude = list(set(selected_ttls.values_list(
				'treatment_type__pk', flat='True')))
			tlengths = tlengths.exclude(
				treatment_type__in=treatment_types_to_exclude) | selected_ttls
		return tlengths


def get_treatment_lengths_locations(healer, locations, treatment_lengths):
	def get_location_treatment_lengths(location_id):
		# def process_treatment_lengths(treatment_lengths):
		# 	return treatment_lengths.select_related('treatment_type')\
		# 		.order_by('treatment_type', 'length')

		l_healer = clients.models.ClientLocation.objects.get(location__pk=location_id).client.healer
		if l_healer == healer:
			return treatment_lengths
		else:
			wcenter = l_healer.wellnesscenter
			l_treatment_types = WellnessCenterTreatmentType.objects.get_or_create(
				wellness_center=wcenter,
				healer=healer)[0].treatment_types.all()
			l_treatment_lengths = TreatmentTypeLength.objects.filter(treatment_type__in=l_treatment_types)
			l_treatment_lengths = exclude_not_selected_treatment_lengths(l_treatment_lengths, wcenter, healer)
		return l_treatment_lengths

	location_ids = [l['id'] for l in locations]
	t_lengths = {}
	for location_id in location_ids:
		t_lengths[location_id] = get_location_treatment_lengths(location_id)
	return t_lengths


def get_providers(healer, order_by_id=False):
	wcenter = is_wellness_center(healer)
	if wcenter:
		providers = get_healers_in_wcenter_with_schedule_editing_perm(healer, order_by_id)
		if wcenter.payment_schedule_setting == WellnessCenter.PAYMENT_EACH_PROVIDER_PAYS:
			return [provider for provider in providers if
				provider.user.has_perm(Healer.SCHEDULE_PERMISSION)]
		else:
			return providers
	else:
		return [healer]


def get_treatments_locations_and_rooms(healer):
	"""Return locations and rooms for treatment types."""
	def get_t_locations_and_rooms(healer):
		all_treatment_types = healer.get_all_treatment_types()
		treatments_locations = {}
		treatments_rooms = {}
		for treatment_type in all_treatment_types:
			treatments_locations[treatment_type.id] = list({room.location.id for
				room in treatment_type.rooms.all()})
			treatments_rooms[treatment_type.id] = [room.as_dict() for
				room in treatment_type.rooms.all()]
		return treatments_locations, treatments_rooms

	providers = get_providers(healer)
	treatments_locations = {}
	rooms = {}
	for provider in providers:
		treatments_locations[provider.user.username], rooms[provider.user.username] = get_t_locations_and_rooms(provider)
	return treatments_locations, rooms


def has_treatments(treatment_lengths, is_wellnesscenter, healer, requesting_healer):
	if len(treatment_lengths) == 0:
		if is_wellnesscenter:
			if healer == requesting_healer:
				return False
		else:
			return False
	return True


def get_username(request, username):
	if username is None:
		return request.user.username
	return username


def get_available_healers(user, wcenter, treatment_type=None, healer=None):
	def check_date():
		today = date.today()
		for timeslot in timeslots:
			if timeslot.end_date is None or timeslot.end_date >= today:
				return True

	def get_allowed_locations():
		if treatment_type is None:
			return get_wcenter_location_ids(wcenter.user)
		return treatment_type.get_available_location_ids() or get_wcenter_location_ids(wcenter.user)

	def healers_to_check():
		if healer is not None:
			healers = [healer]
		else:
			healers = get_visible_healers_in_wcenter(user, wcenter)

		if treatment_type is None:
			return [
				h for h in healers
				if h.get_all_treatment_types(only_center=True)]
		else:
			return [
				h for h in healers
				if treatment_type in h.get_all_treatment_types()]

	def exclude_healers_without_schedule_permission():
		return [healer for healer in available_healers if
			healer.user.has_perm(Healer.SCHEDULE_PERMISSION)]

	available_healers = []

	for healer in healers_to_check():
		timeslots = HealerTimeslot.objects.filter(healer=healer, location__in=get_allowed_locations())
		if check_date():
			available_healers.append(healer)

	available_healers = exclude_healers_without_schedule_permission()
	return available_healers


def get_treatment_length_bar_and_treatment_lengths(treatment_types, treatment_lengths):
	def add_descriptions_to_treatment_lengths(treatment_lengths):
		for tl in treatment_lengths:
			tl.description = tl.treatment_type.description
		return treatment_lengths

	treatment_length_bar = len(treatment_lengths) > len(treatment_types)
	if not treatment_length_bar:
		treatment_lengths = add_descriptions_to_treatment_lengths(
			treatment_lengths)

	return treatment_length_bar, treatment_lengths


def get_tts_ttls_tbar_avail_ttls(user, wellness_center, healer=None, location=None):
	def get_wcenter_treatment_type_lengths():
		wcenter_treatment_type_lengths = WellnessCenterTreatmentTypeLength.objects.filter(wellness_center=wellness_center)
		if healer is not None:
			wcenter_treatment_type_lengths = wcenter_treatment_type_lengths.filter(healer=healer)
		return wcenter_treatment_type_lengths

	def get_wcenter_treatment_types():
		"""Get only available treatment types for center or healer in center if healer argument is set."""
		def remove_treatment_types_without_healer_availability():
			return [
				treatment_type
				for treatment_type in treatment_types
				if get_available_healers(user, wellness_center, treatment_type, healer)
			]

		treatment_types = set()
		wcenter_treatment_types = WellnessCenterTreatmentType.objects.filter(wellness_center=wellness_center)
		if healer is not None:
			wcenter_treatment_types = wcenter_treatment_types.filter(healer=healer)

		for wcenter_treatment_type in wcenter_treatment_types:
			types = wcenter_treatment_type.treatment_types.filter(is_deleted=False)
			if location is not None:
				for type in types:
					if type.is_available_at_location(location):
						treatment_types.add(type)
			else:
				treatment_types |= set(types)

		treatment_types = remove_treatment_types_without_healer_availability()
		treatment_types = sorted(treatment_types, key=lambda u: u.title)
		return treatment_types

	def excude_not_selected_tlengths():
		"""Exclude treatment types which don't have all lengths selected and include selected lengths."""
		def get_selected_lengths():
			lengths = set()
			for wttl in wcenter_treatment_type_lengths:
				ttls = wttl.treatment_type_lengths.all()
				for ttl in ttls:
					lengths.add(ttl.pk)
			return lengths

		def get_wcenter_treatment_type_lengths_types_set():
			"""Treatment types set includes all treatment types where only some of lengths have been selected by healers."""
			treatment_types = set()
			for wttl in wcenter_treatment_type_lengths:
				ttls = wttl.treatment_type_lengths
				if ttls.exists():
					treatment_types.add(ttls.all()[0].treatment_type)
			return treatment_types

		t_lengths = (treatment_lengths.exclude(treatment_type__in=get_wcenter_treatment_type_lengths_types_set()) |
			treatment_lengths.filter(pk__in=get_selected_lengths()))
		return t_lengths

	def exclude_treatment_type_lengths_with_same_treatment_type_and_length():
		type_lengths_added = []  # (type_id, length) tuple of added t_lengths
		t_lengths = []
		for l in treatment_lengths:
			t_l = (l.treatment_type.pk, l.length)
			if t_l not in type_lengths_added:
				type_lengths_added.append(t_l)
				t_lengths.append(l)
		return t_lengths

	wcenter_treatment_type_lengths = get_wcenter_treatment_type_lengths()
	treatment_types = get_wcenter_treatment_types()
	treatment_lengths = TreatmentTypeLength.objects.select_related().filter(
		treatment_type__in=treatment_types, is_deleted=False)
	treatment_lengths = excude_not_selected_tlengths()
	treatment_lengths = exclude_treatment_type_lengths_with_same_treatment_type_and_length()
	treatment_length_bar, treatment_lengths = get_treatment_length_bar_and_treatment_lengths(treatment_types,
		treatment_lengths)
	available_treatment_lengths = json.dumps([l.pk for l in treatment_lengths])

	return treatment_types, treatment_lengths, treatment_length_bar, available_treatment_lengths


def get_timeslot_object(timeslot_id, result=None):
	try:
		timeslot = int(timeslot_id)
		return HealerTimeslot.objects.get(id=timeslot)
	except (ValueError, TypeError):
		error = 'Timeslot id in invalid format.'
	except HealerTimeslot.DoesNotExist:
		error = 'Could not find that timeslot.'
	if result is None:
		return error
	else:
		result.error(error)
		return result.dump()


def create_provider_availabilities_for_timeslot(center, timeslot, healer=None):
	if healer is None:
		healers = get_healers_in_wcenter_with_schedule_editing_perm(center)
	else:
		healers = [healer]
	for healer in healers:
		timeslot.healer = healer
		timeslot.pk = None
		timeslot.save()


def reset_center_and_providers_availabilities(center):
	HealerTimeslot.objects.filter(healer=center).delete()
	for healer in get_healers_in_wcenter_with_schedule_editing_perm(center):
		locations = center.get_location_ids()
		HealerTimeslot.objects.filter(healer=healer, location__in=locations).delete()


def get_location(healer, location_slug):
	if location_slug is not None:
		for l in healer.get_locations_objects():
			if l.slug() == location_slug:
				return l


def get_locations(healer, location_slug=None, selected_location=None, only_visible=None):
	locations = healer.get_locations_objects(only_visible)
	if selected_location is None:
		selected_location = get_location(healer, location_slug)
	return [l for l in locations if selected_location is None or l == selected_location]


def add_user_to_clients(from_user, to_user):
	if not Clients.objects.filter(from_user=from_user, to_user=to_user).exists():  # to fix #1014
		Clients.objects.create(from_user=from_user, to_user=to_user)


def save_phone_number(healer, phone):
	phones = clients.models.ClientPhoneNumber.objects.filter(client=healer)
	if phones:
		phones[0].number = phone
		phones[0].save()
	else:
		clients.models.ClientPhoneNumber.objects.create(client=healer,
														number=phone)
