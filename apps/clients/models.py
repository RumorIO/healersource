import re
from PIL import Image
from datetime import date
import time
import hashlib
from random import random

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, resolve
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.http import Http404
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.text import capfirst, slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from modality.models import Modality, ModalityCategory
from friends.models import Contact, JoinInvitation
from emailconfirmation.models import EmailAddress
from avatar.models import Avatar, remove_avatar_images
from oauth_access.models import UserAssociation
from intake_forms.models import Answer, IntakeFormSentHistory
from clients.utils import client_pic
from ambassador.models import Plan
from util import absolute_url
import healers
import contacts_hs
import send_healing


def is_dummy_user(user):
	return not user.is_active and not user.has_usable_password()


class Client(models.Model):
	LINK_SOURCE_FACEBOOK = 'facebook'
	LINK_SOURCE_INSTAGRAM = 'twitter'
	LINK_SOURCE_TWITTER = 'twitter'
	LINK_SOURCE_LINKEDIN = 'linkedin'
	LINK_SOURCE_GOOGLE = 'google'
	LINK_SOURCE_FRIEND = 'friend'
	LINK_SOURCE_FLYER = 'flyer'
	LINK_SOURCE_OTHER = 'other'
	LINK_SOURCE_CHOICES = (
		(LINK_SOURCE_FACEBOOK, 'Facebook'),
		(LINK_SOURCE_INSTAGRAM, 'Instagram'),
		(LINK_SOURCE_TWITTER, 'Twitter'),
		(LINK_SOURCE_LINKEDIN, 'LinkedIn'),
		(LINK_SOURCE_GOOGLE, 'Google Search'),
		(LINK_SOURCE_FRIEND, 'A Friend'),
		(LINK_SOURCE_FLYER, 'Found a Flyer'),
		(LINK_SOURCE_OTHER, 'Other'),
	)
	GHP_NOTIFICATION_FREQUENCY_EVERY_TIME = 'every time'
	GHP_NOTIFICATION_FREQUENCY_DAILY = 'daily'
	GHP_NOTIFICATION_FREQUENCY_WEEKLY = 'weekly'
	GHP_NOTIFICATION_FREQUENCY_UNSUBSCRIBE = 'unsubscribe'
	GHP_NOTIFICATION_FREQUENCY_CHOICES = (
		(GHP_NOTIFICATION_FREQUENCY_EVERY_TIME, 'Every time I receive healing'),
		(GHP_NOTIFICATION_FREQUENCY_DAILY, 'Once a day'),
		(GHP_NOTIFICATION_FREQUENCY_WEEKLY, 'Once a week'),
		(GHP_NOTIFICATION_FREQUENCY_UNSUBSCRIBE, 'Unsubscribe'),
	)

	SIGNUP_SOURCE_NOTES_LP = 'notes_lp'
	SIGNUP_SOURCE_HOMEPAGE = 'homepage'
	# SIGNUP_SOURCE_REFERRAL = 'referral'
	SIGNUP_SOURCE_APP = 'app'

	SIGNUP_SOURCE_CHOICES = (
		(SIGNUP_SOURCE_NOTES_LP, 'Notes Landing Page'),
		(SIGNUP_SOURCE_HOMEPAGE, 'Homepage'),
		# (SIGNUP_SOURCE_REFERRAL, 'Referral'),
		(SIGNUP_SOURCE_APP, 'App'),
	)

	user = models.OneToOneField(User)
	is_deleted = models.BooleanField(default=False)
	approval_rating = models.PositiveIntegerField(default=0)
	about = models.TextField(_("about"), blank=True, default="")
	referred_by = models.CharField(max_length=255, blank=True)
	invite_message = models.TextField(blank=True, default="")
	beta_tester = models.BooleanField(default=True)
	send_reminders = models.BooleanField(default=True)
	ghp_notification_frequency = models.CharField(max_length=32,
		choices=GHP_NOTIFICATION_FREQUENCY_CHOICES, default="every time")

	website = models.CharField(max_length=255, blank=True, default="")
	facebook = models.CharField(max_length=255, blank=True, default="")
	twitter = models.CharField(max_length=255, blank=True, default="")
	google_plus = models.CharField(max_length=255, blank=True, default="")
	linkedin = models.CharField(max_length=255, blank=True, default="")
	yelp = models.CharField(max_length=255, blank=True, default="")

	first_login = models.BooleanField(default=True)

	date_modified = models.DateTimeField(default=timezone.now)
	link_source = models.CharField(max_length=32, choices=LINK_SOURCE_CHOICES, blank=True, null=True, default="")
	signup_source = models.CharField(max_length=32,
		choices=SIGNUP_SOURCE_CHOICES, blank=True, null=True, default=SIGNUP_SOURCE_HOMEPAGE)

	ambassador = models.ForeignKey('self', blank=True, null=True)
	ambassador_plan = models.ForeignKey(Plan, blank=True, null=True)
	ambassador_program = models.BooleanField(default=False)
	utm_source = models.CharField(max_length=255, blank=True, null=True)
	utm_medium = models.CharField(max_length=255, blank=True, null=True)
	utm_term = models.CharField(max_length=255, blank=True, null=True)
	utm_campaign = models.CharField(max_length=255, blank=True, null=True)
	utm_content = models.CharField(max_length=255, blank=True, null=True)

	embed_background_color = models.CharField(max_length=7, blank=True)
	embed_search_all = models.BooleanField(default=True)

	objects = gis_models.GeoManager()

	class Meta:
		verbose_name = _("client")
		verbose_name_plural = _("clients")

	def get_full_url(self, view='client_public_profile', absolute=True):
		url = u''
		if absolute:
			url = absolute_url()

		if view == 'healer_public_profile':
			url += u'%s' % (
				reverse(view, args=[
					slugify(self.default_location), slugify(self.default_modality),
					slugify(self.user.username)
				])
			)
		else:
			url += u'%s' % (
				reverse(view, args=(self.user.username,)),
			)
		return url

	def contact_info(self, separator='\n', email_link=False):
		phones = ClientPhoneNumber.objects.filter(client=self)
		info = [unicode(phone) for phone in phones]

		if self.user.email:
			if email_link:
				info.append('<a href="mailto:' + self.user.email + '">' + self.user.email + '</a>')
			else:
				info.append(self.user.email)

		return separator.join(info)

	def get_contact_info(self, healer):
		try:
			return self.contactinfo_set.filter(healer=healer)[0]
		except IndexError:
			return None

	def first_phone(self):
		phones = ClientPhoneNumber.objects.filter(client=self)
		return phones[0].number_only() if phones else ""

	def linkify(self, link):
		if link.startswith("http://") or link.startswith("https://"):
			return link
		else:
			return "%s%s" % (settings.DEFAULT_HTTP_PROTOCOL, link)

	def website_link(self):
		return self.linkify(self.website)

	def facebook_link(self):
		return self.linkify(self.facebook)

	def twitter_link(self):
		return self.linkify(self.twitter)

	def google_plus_link(self):
		return self.linkify(self.google_plus)

	def linkedin_link(self):
		return self.linkify(self.linkedin)

	def yelp_link(self):
		return self.linkify(self.yelp)

	def __unicode__(self):
		if self.user.first_name == '' and self.user.last_name == '':
			return self.user.username
		else:
			return ("%s %s" % (capfirst(self.user.first_name), capfirst(self.user.last_name))).strip()

	def is_dummy(self):
		return is_dummy_user(self.user)

	def has_confirmed_email(self):
		return EmailAddress.objects.filter(user=self.user, verified=True).count() > 0

	def username(self):
		if self.is_dummy():
			return self.__unicode__()
		else:
			return self.user.username

	def healing_sent(self):
		seconds = sum(send_healing.models.SentHealing.objects.filter(sent_by=self).values_list(
			"duration", flat=True))
		return send_healing.utils.seconds_to_h_m(seconds)

	def healing_sent_to_num_people(self):
		return send_healing.models.SentHealing.total_healing_sent_to_num_people(self)

	def healing_received(self, in_seconds=True):
		def get_seconds(qset):
			return qset.aggregate(total=models.Sum('duration'))['total']

		try:
			fb_obj = self.user.userassociation_set.get(service='facebook')
			contacts = Contact.objects.filter(contactsocialid__social_id=fb_obj.identifier.split('-')[1])
			contact_content_type = ContentType.objects.get(app_label='friends', model='contact')
			sent_healing = send_healing.models.SentHealing.objects.filter(person_content_type=contact_content_type,
					person_object_id__in=contacts)
		except UserAssociation.DoesNotExist:
			sent_healing = send_healing.models.SentHealing.objects.none()
		client_content_type = ContentType.objects.get(app_label='clients', model='client')
		sent_healing |= send_healing.models.SentHealing.objects.filter(person_content_type=client_content_type,
				person_object_id=self.pk)

		if in_seconds:
			return send_healing.utils.seconds_to_h_m(get_seconds(sent_healing))
		else:
			return sent_healing

	def healing_received_from_num_people(self):
		return self.healing_received(in_seconds=False).distinct('sent_by').count()

	def answered_intake_form(self, healer):
		intake_forms = healer.intake_forms.all()
		if intake_forms:
			intake_form = intake_forms[0]
		else:
			return False

		answers_by_client = intake_form.answer_set.filter(client=self)
		return True if answers_by_client.count() > 0 else False

	def incomplete_intake_form_answers(self):
		return Answer.objects.filter(client=self, complete=False)

	def completed_forms(self):
		return self.intake_form_answers.all()

	def incomplete_forms(self):
		incomplete = []
		for instance in IntakeFormSentHistory.objects.filter(client=self).distinct('healer'):
			forms = instance.healer.intake_forms.all()
			if forms.count() == 0:
				continue
			form = forms[0]

			try:
				form.answer_set.get(client=instance.client)
			except Answer.DoesNotExist:
				incomplete.append(instance)
		return incomplete

	def get_locations_objects(self):
		c_location_list = ClientLocation.objects.filter(client=self, location__is_deleted=False).order_by('-location__is_default')
		return [c_location.location for c_location in c_location_list]

	def has_enabled_stripe_connect(self):
		return UserAssociation.objects.filter(user=self.user, service='stripe').exists()

	def stripe_api_key(self):
		return UserAssociation.objects.get(user=self.user, service='stripe').identifier

	def is_referrals_group(self):
		"""
		Is referrals organize group - wellness center, school, etc.
		"""
		try:
			self.healer.wellnesscenter
			return True
		except AttributeError:
			pass
		return False


class ClientPhoneNumber(models.Model):
	client = models.ForeignKey(Client, related_name="phone_numbers")
	type = models.CharField(max_length=42, default="Mobile")
	number = models.CharField(max_length=42)

	def number_only(self):
		return self.number

	def __unicode__(self):
		return "%s: %s" % (self.type, self.number)


class ClientLocation(models.Model):
	client = models.ForeignKey(Client)
	location = models.ForeignKey('healers.Location')

	objects = gis_models.GeoManager()

	def __unicode__(self):
		return "%s" % (self.location)

	class Meta:
		ordering = ["location"]


class Gallery(models.Model):
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey('content_type', 'object_id')
	order = models.PositiveSmallIntegerField()
	client = models.ForeignKey(Client)
	hidden = models.BooleanField(default=False)

	class Meta:
		get_latest_by = 'id'

	def save(self, *args, **kwargs):
		if not self.order:
			gallery_count = self.client.gallery_set.count()
			self.order = gallery_count + 1
		super(Gallery, self).save(*args, **kwargs)

	def is_photo(self):
		photo_content_type = ContentType.objects.get(app_label='avatar', model='avatar')
		# video_content_type = ContentType.objects.get(app_label='clients', model='clientvideo')
		return self.content_type == photo_content_type

	def rotate(self, direction):
		if self.is_photo():
			def get_angle():
				if direction == 'right':
					return -90
				elif direction == 'left':
					return 90

			avatar_object = self.content_object
			path = avatar_object.avatar.path

			image = Image.open(path)
			image = image.rotate(get_angle())
			remove_avatar_images(instance=self.content_object)
			image.save(path)
			with open(path, 'r') as f:
				avatar_object.avatar.storage.save(path, f)
				avatar_object.save()

	def change_order(self, order):
		order = int(order)
		if order == self.order:
			return
		old_order = self.order

		if order > old_order:
			other_videos = self.client.gallery_set.filter(order__gt=old_order, order__lte=order).order_by('order')
		else:
			other_videos = self.client.gallery_set.filter(order__gte=order, order__lt=old_order).order_by('order')

		if order > old_order:
			i = old_order
		else:
			i = order
		for video in other_videos:
			if order < old_order:
				i += 1
			video.order = i
			video.save()
			if order > old_order:
				i += 1

		self.order = order
		if order == 1:
			self.hidden = False
		self.save()
		if order == 1:
			Gallery.set_first_photo_as_avatar(self.client)

	@classmethod
	def get_first_item(kls, client):
		gallery_items = client.gallery_set.all().order_by('order')
		if gallery_items.exists():
			return gallery_items[0]

	@classmethod
	def set_first_photo_as_avatar(kls, client):
		first_item = Gallery.get_first_item(client)
		if first_item is not None and first_item.is_photo():
			avatar = first_item.content_object
			avatar.primary = True
			avatar.save()

	@classmethod
	def update_order(kls, client):
		items = client.gallery_set.all().order_by('order')
		i = 1
		for item in items:
			if item.order != i:
				if i == 1:
					item.hidden = False
				item.order = i
				item.save()
			i += 1
		Gallery.set_first_photo_as_avatar(client)


class ClientVideo(models.Model):
	VIDEO_TYPE_GALLERY = 1
	VIDEO_TYPE_CLIENT = 2

	VIDEO_TYPE_CHOICES = (
		(VIDEO_TYPE_GALLERY, 'Gallery Video'),
		(VIDEO_TYPE_CLIENT, 'Client Video'),
	)

	client = models.ForeignKey(Client, related_name='videos')
	url = models.URLField()
	title = models.CharField(max_length=255)
	date_added = models.DateTimeField()
	video_id = models.CharField(max_length=255)
	videotype = models.PositiveSmallIntegerField(
		choices=VIDEO_TYPE_CHOICES, null=True, blank=True)

	def embed(self):
		return render_to_string('clients/youtube_embed.html', {'video_id': self.video_id})

	def __unicode__(self):
		return self.title

	class Meta:
		ordering = ["-date_added"]


class SiteJoinInvitationManager(models.Manager):

	def create(self, **kwargs):
		if not 'confirmation_key' in kwargs:
			key = kwargs.pop('key', False)
			if not key:
				contact = kwargs.get('contact', False)
				if contact:
					key = contact.email
			if key:
				salt = hashlib.sha1(str(random())).hexdigest()[:5]
				kwargs['confirmation_key'] = hashlib.sha1(salt + str(key)).hexdigest()

		return super(SiteJoinInvitationManager, self).create(**kwargs)

	def send_invitation(self, from_user, to_email, message="",
			html_template_name=None, subject_template=None, body_template=None,
			is_to_healer=False, is_from_site=False, to_name=None,
			create_friendship=True, is_for_ambassador=False,
			send_intake_form=False, intake_form_receiver_client=None,
			**extra_context):

		def get_accept_url():
			if is_for_ambassador:
				url = reverse('ambassador:signup', kwargs={'username': from_user})
			else:
				url = invitation.accept_url(send_intake_form)
			return absolute_url(url)

		if not to_email:
			return

		invitation = None
		invitation_exist = False
		contact, created = Contact.objects.get_or_create(email=to_email, user=from_user)
		if not created:
			try:
				invitation = self.get(from_user=from_user, contact=contact)
				invitation.confirmation_key
				invitation_exist = True
			except SiteJoinInvitation.DoesNotExist:
				pass
			to_name = contact.name
		elif to_name:
			contact.name = to_name
			contact.save()

		if not invitation_exist:
			invitation = self.create(from_user=from_user, contact=contact, message=message, status="2",
							key=to_email, is_from_site=is_from_site, is_to_healer=is_to_healer,
							create_friendship=create_friendship)

		accept_url = get_accept_url()
		if send_intake_form:
			from_user.client.healer.send_intake_form(intake_form_receiver_client, accept_url)
			return

		ctx = {
			"SITE_NAME": settings.SITE_NAME,
			"SITE_DOMAIN": Site.objects.get_current().domain,
			"STATIC_URL": settings.STATIC_URL,
			"CONTACT_EMAIL": settings.CONTACT_EMAIL,
			"user": from_user,
			"from_user_name": str(from_user.client),
			"to_email": to_email,
			"to_name": to_name,
			"message": message,
			"accept_url": accept_url,
			"review_url": absolute_url(reverse('review_form', kwargs={'username': from_user})),
		}
		ctx.update(extra_context)

		if not (healers.utils.is_healer(from_user) and not from_user.client.healer.review_permission == healers.models.Healer.VISIBLE_DISABLED):
			ctx['review_url'] = ''

		if is_to_healer:
			if create_friendship:
				_subject_template = "friends/join_invite_recommend_subject.txt"
				_body_template = "friends/join_invite_recommend_message.txt"
			else:
				_subject_template = "friends/join_invite_subject.txt"
				_body_template = "friends/join_invite_message.txt"
		else:
			_subject_template = "friends/client_join_invite_subject.txt"
			_body_template = "friends/client_join_invite_message.txt"

		if is_for_ambassador:
			_subject_template = "friends/join_invite_subject.txt"

		#These are for unregistered bookings - both brand new user and new user who tries to book a 2nd appointment
		if is_from_site:
			_subject_template = "account/emails/invite_user_subject.txt"
			_body_template = "account/emails/invite_user_message.txt"

		subject_template = subject_template if subject_template else _subject_template
		body_template = body_template if body_template else _body_template

		subject = render_to_string(subject_template, ctx)

		healers.utils.send_hs_mail(subject, body_template, ctx, settings.DEFAULT_FROM_EMAIL, [to_email], html_template_name=html_template_name)
		return invitation


class SiteJoinInvitation(JoinInvitation):
	"""
	Extended JoinInvitation to allow send invites from site
	"""
	is_from_site = models.BooleanField(default=False)
	is_to_healer = models.BooleanField(default=False)
	create_friendship = models.BooleanField(default=True)

	objects = SiteJoinInvitationManager()

	def accept_url(self, intake_form=False):
		if intake_form:
			url = 'friends_accept_join_intake'
		else:
			url = 'friends_accept_join'
		return reverse(url, args=(self.confirmation_key,))


def create_dummy_user(first_name, last_name, email, commit=True,
						create_real_username=False):
	""" Creates user with timestamp username and unusable password """

	def get_username():
		def get_real_username():
			def is_unique_username(username):
				if User.objects.filter(username=username).exists():
					return False

				try:
					match = resolve('/%s/' % username)
					if match[0] != healers.views.healer:
						return False
				except Http404:
					pass
				if((Modality.objects_approved.filter(title__iexact=username).count() > 0)
						or (ModalityCategory.objects.filter(title__iexact=username).count() > 0)):
					return False
				return True

			def get_numbered_username(username, n=None):
				def get_username_and_n():
					match = re.match('^(.+?)(\d+)$', username)
					if match is None:
						return username, 1
					else:
						return match.group(1), int(match.group(2))

				if n is None:
					username, n = get_username_and_n()
				numbered_username = '%s%d' % (
					username[:settings.USERNAME_MAX_LENGTH - len(str(n))], n)
				if is_unique_username(numbered_username):
					return numbered_username
				else:
					n += 1
					return get_numbered_username(username, n)

			def get_username():
				def generate_username_from_name():
					fname = first_name.encode('utf-8').decode('ascii', 'ignore')
					lname = last_name.encode('utf-8').decode('ascii', 'ignore').strip()

					if lname and fname:
						return '%s_%s' % (fname, lname)
					elif lname:
						return lname
					else:
						return fname

				username = generate_username_from_name().strip('/')
				if len(username) < settings.USERNAME_MIN_LENGTH:
					username = email.replace('@', '_at_')
				if len(username) > settings.USERNAME_MAX_LENGTH:
					username = username[:settings.USERNAME_MAX_LENGTH]

				return username.replace(' ', '_').replace('.', '_').lower()

			username = get_username()

			if not is_unique_username(username):
				username = get_numbered_username(username)

			return username

		def get_timestamp_username():
			i = 1
			while (i < 100):
				timestamp = str(time.time())
				users = User.objects.filter(username=timestamp)

				if len(users) == 0:
					return timestamp
				else:
					i += 1

		if create_real_username:
			return get_real_username()
		return get_timestamp_username()

	user = User(username=get_username(), first_name=first_name[:30], last_name=last_name[:30], email=email.strip().lower(), is_active=False)
	user.set_unusable_password()

	if commit:
		user.save()

	return user


class ReferralsSent(models.Model):
	PROVIDER_TO_CLIENT = 0
	CLIENT_TO_PROVIDER = 1

	TYPE_CHOICES = (
		(PROVIDER_TO_CLIENT, 'Provider To Client'),
		(CLIENT_TO_PROVIDER, 'Client to Provider')
	)

	provider_user = models.ForeignKey(User, related_name='referral_provider')
	client_user = models.ForeignKey(User, null=True, related_name='referral_client')
	referring_user = models.ForeignKey(User, related_name='referral_sender')
	client_email = models.EmailField(max_length=255, null=True) #not currently used
	type = models.PositiveSmallIntegerField(default=PROVIDER_TO_CLIENT, choices=TYPE_CHOICES)
	message = models.TextField(null=True, blank=True, default=None)
	date_sent = models.DateField(default=date.today)

	class Meta:
		unique_together = (('provider_user', 'client_user', 'referring_user'),)


class PersonAbstract(models.Model):
	person_content_type = models.ForeignKey(ContentType)
	person_object_id = models.PositiveIntegerField()
	person = generic.GenericForeignKey('person_content_type', 'person_object_id')

	def type(self):
		contact_content_type = ContentType.objects.get(app_label='friends', model='contact')
		if self.person_content_type == contact_content_type:
			return 'contact'
		else:
			return 'client'

	def full_name(self):
		if self.type() == 'contact':
			return self.person.name
		else:
			return unicode(self.person)

	def get_email(self):
		if self.type() == 'contact':
			return self.person.email
		else:
			return self.person.user.email

	def phone(self):
		if self.type() == 'contact':
			contact_phone = contacts_hs.models.ContactPhone.objects.filter(contact=self.person)
			if contact_phone.exists():
				return contact_phone[0].number
			return ''
		else:
			return self.person.first_phone()

	def avatar(self):
		return client_pic(self.type(), self.person)

	def __unicode__(self):
		return self.full_name()

	class Meta:
		abstract = True


#def create_profile(sender, instance, created, **kwargs):
#	if instance is None:
#		return
#
#	if created:
#		profile, created = Client.objects.get_or_create(user=instance)

#post_save.connect(create_profile, sender=User)


# def delete_gallery_video(sender, instance, **kwargs):
# 	if instance.videotype != ClientVideo.VIDEO_TYPE_GALLERY:
# 		return
# 	try:
# 		content_type = ContentType.objects.get(app_label="clients", model="clientvideo")
# 		gallery = Gallery.objects.get(content_type=content_type, object_id=instance.id)
# 		gallery.delete()
# 		Gallery.update_order(instance.client)
# 	except Gallery.DoesNotExist:
# 		pass

# pre_delete.connect(delete_gallery_video, sender=ClientVideo)

# def delete_gallery_avatar(sender, instance, **kwargs):
# 	content_type = ContentType.objects.get(app_label="avatar", model="avatar")
# 	try:
# 		gallery = Gallery.objects.get(content_type=content_type, object_id=instance.id)
# 		gallery.delete()
# 		Gallery.update_order(instance.user.client)
# 	except Gallery.DoesNotExist:
# 		pass

# pre_delete.connect(delete_gallery_avatar, sender=Avatar)

def delete_gallery_item(sender, instance, **kwargs):
	content_object = instance.content_object
	if content_object:
		content_object.delete()
	Gallery.update_order(instance.client)

post_delete.connect(delete_gallery_item, sender=Gallery)


def create_gallery_avatar(sender, instance, **kwargs):
	def client_already_has_avatar():
		items = Gallery.objects.filter(client=client)
		for item in items:
			if (item.is_photo() and item.content_object and
					item.content_object.avatar == instance.avatar):
				return True
		return False

	client = instance.user.client

	if not client_already_has_avatar():
		Gallery.objects.create(content_object=instance,
			client=client)

post_save.connect(create_gallery_avatar, sender=Avatar)
