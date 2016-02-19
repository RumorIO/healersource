import json
import re
import urllib2
import dateutil.parser
import feedparser
from datetime import datetime
from time import mktime

from django.conf import settings
from django import forms
from django.contrib.auth.models import User
from django.template.defaultfilters import title

from contacts_hs.models import ContactPhone, ContactEmail
from healers.models import Location, Zipcode
from clients.models import Client, ClientPhoneNumber, ClientVideo, Gallery
from healers.utils import html_sanitize
from util.widgets import TinyEditor


class AboutClientForm(forms.Form):
	about = forms.CharField(label="About Me", required=False, widget=TinyEditor())

	def clean_about(self):
		return html_sanitize(self.cleaned_data['about'])


class RemoteSessionsForm(forms.Form):
	remote_sessions = forms.BooleanField(required=False,
		label="Do you provide remote sessions - Phone, Online, Skype, or Distance Healing, etc?")


class ShortClientForm(AboutClientForm):
	email = forms.EmailField(label='Email', required=False)
	password = forms.CharField(label='Password', required=False)
	first_name = forms.CharField(label='First Name', max_length=30, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
	location = forms.CharField(label='Location', max_length=42, required=False)


class ClientForm(AboutClientForm, RemoteSessionsForm):
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
	last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}), required=False)
	phone = forms.CharField(required=False, label="Phone Number", max_length=30, widget=forms.TextInput())
	send_reminders = forms.BooleanField(label="Send me an Appointment Reminder the day before", required=False)
	ghp_notification_frequency = forms.ChoiceField(required=False, label="Healing Circle Notifications", choices=Client.GHP_NOTIFICATION_FREQUENCY_CHOICES)


class ContactInfoForm(forms.Form):
	first_name = forms.CharField(max_length=30, widget=forms.TextInput())
	last_name = forms.CharField(max_length=30, widget=forms.TextInput())
	phone = forms.CharField(max_length=30, required=False, label=u'Phone Number',
		widget=forms.TextInput(attrs={'size': '56'}))
	email = forms.EmailField(label=u'Email', required=False, widget=forms.TextInput(attrs={'size': '18'}))
	address_line1 = forms.CharField(max_length=42, required=False, label='Address Line 1')
	address_line2 = forms.CharField(max_length=42, required=False, label='Address Line 2')
	postal_code = forms.CharField(max_length=10, required=False, label='Zip Code')
	city = forms.CharField(max_length=42, required=False)
	state_province = forms.CharField(max_length=42, required=False, label='State')
	country = forms.CharField(max_length=42, required=False, label='Country')

	def __init__(self, *args, **kwargs):
		self.instance = kwargs.pop('contact_info')
		initial = kwargs.pop('initial', {})
		initial['first_name'] = self.instance.first_name
		initial['last_name'] = self.instance.last_name
		initial['address_line1'] = self.instance.address_line1
		initial['address_line2'] = self.instance.address_line2
		initial['postal_code'] = self.instance.postal_code
		initial['city'] = self.instance.city
		initial['state_province'] = self.instance.state_province
		initial['country'] = self.instance.country

		try:
			initial['phone'] = self.instance.phone_numbers.all()[0].number
		except IndexError:
			pass
		try:
			initial['email'] = self.instance.emails.all()[0].email
		except IndexError:
			pass
		kwargs['initial'] = initial
		super(ContactInfoForm, self).__init__(*args, **kwargs)

	def save(self):
		contact_info = self.instance
		if not contact_info.client.user.is_active:
			contact_info.first_name = self.cleaned_data['first_name']
			contact_info.last_name = self.cleaned_data['last_name']

		contact_info.address_line1 = self.cleaned_data['address_line1']
		contact_info.address_line2 = self.cleaned_data['address_line2']
		contact_info.postal_code = self.cleaned_data['postal_code']
		contact_info.city = self.cleaned_data['city']
		contact_info.state_province = self.cleaned_data['state_province']
		contact_info.country = self.cleaned_data['country']
		contact_info.save()
		try:
			phone = self.instance.phone_numbers.all()[0]
		except IndexError:
			phone = ContactPhone(contact=self.instance)
		phone.number = self.cleaned_data['phone']
		phone.save()

		try:
			email = self.instance.emails.all()[0]
		except IndexError:
			email = ContactEmail(contact=self.instance)
		email.email = self.cleaned_data['email']
		email.save()


class PhoneForm(forms.Form):
	phone_number = forms.CharField(
		label="Number",
		required=True,
		widget=forms.TextInput(attrs={"size": "30"})
	)

	phone_type = forms.CharField(
		label="Type",
		required=False,
		widget=forms.TextInput(attrs={"size": "30"})
	)

	def save(self, client):
		phone = ClientPhoneNumber()
		phone.client = client
		phone.number = self.cleaned_data['phone_number']
		if self.cleaned_data['phone_type']:
			phone.type = self.cleaned_data['phone_type']
		phone.save()
		return phone


class VideoForm(forms.Form):
	video_url = forms.CharField(label="YouTube video", min_length=16, required=True)
	videotype = forms.CharField(widget=forms.HiddenInput())

	def clean(self):
		cleaned_data = super(VideoForm, self).clean()
		video_url = cleaned_data.get('video_url', False)
		if not video_url:
			return cleaned_data
		try:
			if video_url.find('youtu.be') != -1:
				self.video_id = video_url[video_url.rfind('/')+1:]

			elif video_url.find('youtube.com') != -1:
				r = re.search(r'[&?]{1}v=([^&]*)', video_url)
				self.video_id = r.group(1)

			fp = urllib2.urlopen('https://www.googleapis.com/youtube/v3/videos?id=%s&key=%s&part=snippet' % (self.video_id, settings.GOOGLE_API_KEY))
			data = fp.read()
			data = json.loads(data)
			self.title = data['items'][0]['snippet']['title']
			self.date_added = dateutil.parser.parse(data['items'][0]['snippet']['publishedAt'])
			self.videotype = cleaned_data.get('videotype', None)
		except Exception as e:
			raise forms.ValidationError("Can't load video data. %s" % e)

		return cleaned_data

	def save(self, client):
		video_url = self.cleaned_data['video_url']
		video = client.videos.create(
			url=video_url,
			video_id=self.video_id,
			title=self.title,
			date_added=self.date_added,
			videotype=self.videotype)

		if int(self.videotype) == ClientVideo.VIDEO_TYPE_GALLERY:
			Gallery.objects.create(content_object=video, client=client)

		return video


class UploadedVideosImportForm(forms.Form):
	youtube_username = forms.CharField(label="YouTube username", min_length=6, required=True)

	def save(self, client):
		import_url = 'https://gdata.youtube.com/feeds/api/users/%s/uploads?v=2' % self.cleaned_data['youtube_username']
		d = feedparser.parse(import_url)
		for entry in d['entries']:
			client.videos.create(
				url=entry.link,
				video_id=entry.yt_videoid,
				title=entry.title,
				date_added=datetime.fromtimestamp(mktime(entry.published_parsed)))


class SendReferralForm(forms.Form):
	to_username = forms.CharField()
	from_username = forms.CharField()
	message = forms.CharField()
	client_or_healer = forms.IntegerField()

	def clean(self):
		cleaned_data = super(SendReferralForm, self).clean()

		try:
			cleaned_data['to_user'] = User.objects.get(username__iexact=cleaned_data['to_username'])

		except KeyError:
			raise forms.ValidationError("You must select someone to refer to.")

		except User.DoesNotExist:
			raise forms.ValidationError("Could not find user %s." % cleaned_data['to_username'])

		return cleaned_data


class ClientLocationForm(forms.ModelForm):
	class Meta:
		model = Location
		fields = ('title', 'address_line1', 'address_line2',
					'city', 'state_province', 'postal_code', 'country')

	def save(self, **kwargs):
		commit = kwargs.pop('commit', True)
		location = super(ClientLocationForm, self).save(commit=False)
		if not self.cleaned_data['title']:
			location.title = self.cleaned_data['address_line1']

		if self.cleaned_data['postal_code']:
			zip_code = Zipcode.objects.filter(
				code=self.cleaned_data['postal_code'])
			if len(zip_code) > 0:
				zip_code = zip_code[0]
				location.city = title(zip_code.city)
				location.state_province = zip_code.state
				if (self.cleaned_data['postal_code'] == self.cleaned_data['title'] or
					location.title == '%s, %s' % (self.cleaned_data['city'],
						self.cleaned_data['state_province'])):
					location.title = '%s, %s' % (location.city,
						location.state_province)

		location.google_maps_request()
		if commit:
			location.save()
		return location
