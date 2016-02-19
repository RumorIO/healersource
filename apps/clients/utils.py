import re
import os

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import SafeText

from avatar.templatetags.avatar_tags import avatar
from avatar.conf import settings as avatar_settings
from util import absolute_url
import clients


def get_avatar(user, size, external=False, get_url=False, phonegap=False, no_size=False):
	""" Return avatar tag and external url if get_url is True no matter what external value is.
	If phonegap is True return local avatar."""
	def get_external():
		if external:
			return 'data-external'
		else:
			return ''

	if type(user) == SafeText:
		users = User.objects.filter(username=user)
		if users.exists():
			user = users[0]
		else:
			user = None

	if user is not None:
		first_item = clients.models.Gallery.get_first_item(user.client)
		if first_item is not None and not first_item.is_photo() and not phonegap:
			url = 'https://img.youtube.com/vi/{}/0.jpg'.format(first_item.content_object.video_id)
			if get_url:
				return url
			else:
				if no_size is True:
					return '<img src="{0}" {1}>'.format(url, get_external())
				else:
					return '<img src="{0}" width="{1}" height="{1}" {2}>'.format(url, size, get_external())

	tag = avatar(user, size)
	url = re.match('.+?src="(.+?)"', tag).group(1)
	if no_size is True:
		tag = tag.replace('width="{0}" height="{0}"'.format(size), '')
	external_url = absolute_url(url)
	if get_url:
		return external_url
	else:
		if external:
			tag = tag.replace(url, external_url)
		if phonegap:
			tag = tag.replace(url, 'img/avatars/{}.jpg'.format(user.username))
		return tag


def client_pic(type, obj):
	def get_user():
		if obj is not None:
			return obj.user

	height = 350
	if type == 'contact':
		try:
			social_obj = obj.contactsocialid_set.filter(service='facebook')[0]
			return social_obj.fb_profile_pic(height=height)
		except IndexError:
			return ''
	elif type == 'client':
		return get_avatar(get_user(), height, get_url=True)


def get_person_content_type(type):
	if type == 'client':
		return ContentType.objects.get(app_label='clients', model='client')
	elif type == 'contact':
		return ContentType.objects.get(app_label='friends', model='contact')


def avatar_file_path(user, type, name):
	def fix_filename(type, name):
		def is_correct_extension(name):
			name = name.lower()
			if type == 'jpeg':
				return name.endswith('.jpg') or name.endswith('.jpeg')
			else:
				return name.endswith('.' + type)

		# extension type is already checked
		if type is None:
			return name
		if is_correct_extension(name):
			return name
		else:
			return '%s.%s' % (name, type)

	path = [avatar_settings.AVATAR_STORAGE_DIR]
	path.append(user.username)
	path.append(fix_filename(type, name))
	return os.path.join(*path)
