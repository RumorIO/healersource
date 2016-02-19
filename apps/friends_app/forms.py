import re
import os

from django import forms
from django.conf import settings
# from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from django.utils.encoding import smart_unicode

from healers.models import Healer
from friends.models import *
from friends.importer import import_vcards
# from friends.forms import JoinRequestForm

# @@@ move to django-friends when ready

class ImportVCardForm(forms.Form):
	vcard_file = forms.FileField(label="vCard File")

	def save(self, user):
		imported, total = import_vcards(self.cleaned_data["vcard_file"].content, user)
		return imported, total

validate_email = EmailValidator('Enter a valid email addresses.', 'invalid')

class JoinInviteRequestForm(forms.Form):
	emails = forms.CharField(label="Enter email addresses of the people you would like to invite", required=True, widget=forms.Textarea(attrs={'cols': '30', 'rows': '5'}),
	                         help_text="One email per line, or separated by a comma or semicolon.")
	message = forms.CharField(label="Message", required=False, widget=forms.Textarea(attrs={'cols': '30', 'rows': '5'}))
	invite_type = forms.ChoiceField(label="Invite As", widget=forms.RadioSelect(),
	                                choices=(("client", "Clients"), ("provider", "Referrals")) )

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		imported_contacts = kwargs.pop('imported_contacts', None)
		super(JoinInviteRequestForm, self).__init__(*args, **kwargs)
		if imported_contacts:
			contacts = Contact.objects.filter(id__in=imported_contacts).values_list('email')
			self.fields['emails'].initial = "\n".join([o[0] for o in contacts])

	def clean_emails(self):
		""" Split and validate emails """
		email_list = re.split('[\s,;]+', self.cleaned_data['emails'].strip())
		for email in email_list:
			validate_email(email)
		return email_list

class MultipleEmailField(forms.Field):
	widget = forms.MultipleHiddenInput
	default_error_messages = {
		'invalid_list': u'Enter a list of values.',
		}

	def to_python(self, value):
		if not value:
			return []
		elif not isinstance(value, (list, tuple)):
			raise ValidationError(self.error_messages['invalid_list'])
		return [smart_unicode(val) for val in value]

	def clean(self, value):
		value = self.to_python(value)
		self.validate(value)
		cleaned_value = []
		for val in value:
			try:
				validate_email(val)
				cleaned_value.append(val)
			except ValidationError:
				pass
		return cleaned_value

	def validate(self, value):
		if self.required and not value:
			raise ValidationError(self.error_messages['required'])

class PostcardBackgroundField(forms.ChoiceField):

	def __init__(self, *args, **kwargs):
		super(PostcardBackgroundField, self).__init__(*args, **kwargs)
		if not self.choices:
			self.update_choices()
		if not self.initial:
			try:
				self.initial = self.choices[0][0]
			except IndexError:
				pass

	def update_choices(self):
		files = os.listdir(settings.INVITATION_BACKGROUND_ROOT)
		self.choices = [(f, os.path.splitext(f)[0]) for f in files
		                if os.path.splitext(f)[1].lower() in ('.jpg', '.jpeg', '.png')]

	def clean(self, value):
		value = super(PostcardBackgroundField, self).clean(value)
		return settings.INVITATION_BACKGROUND_URL + value

class PostcardJoinInviteRequestForm(JoinInviteRequestForm):
	INVITATION_BACKGROUND_URL = settings.INVITATION_BACKGROUND_URL
	postcard_background = PostcardBackgroundField(label="Choose Background", initial=settings.DEFAULT_INVITATION_BACKGROUND)
	invite_provider_recommend = forms.BooleanField(required=False, widget=forms.HiddenInput(), initial=True)

	def __init__(self, *args, **kwargs):
		super(PostcardJoinInviteRequestForm, self).__init__(*args, **kwargs)
		self.fields['invite_type'].widget = forms.HiddenInput()
		self.fields['postcard_background'].update_choices()

class ContactsJoinInviteRequestForm(forms.Form):
	INVITATION_BACKGROUND_URL = settings.INVITATION_BACKGROUND_URL

	providers = forms.ModelMultipleChoiceField(queryset=Healer.objects.exclude(profileVisibility=Healer.VISIBLE_CLIENTS), required=False)
	contacts = forms.ModelMultipleChoiceField(queryset=Contact.objects.none(), required=False)
	email_list = MultipleEmailField(required=False)
	message = forms.CharField(label="Message",
	                          required=False,
	                          widget=forms.Textarea(attrs={'placeholder': 'Type your message here'}))
	invite_type = forms.ChoiceField(label="Invite As", widget=forms.HiddenInput(),
	                                choices=(("client", "Client"), ("provider", "Provider")) )
	invite_provider_recommend = forms.BooleanField(required=False, widget=forms.HiddenInput(), initial=True)
	postcard_background = PostcardBackgroundField(label="Choose Background", initial=settings.DEFAULT_INVITATION_BACKGROUND)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		imported_contacts = kwargs.pop('imported_contacts', None)
		super(ContactsJoinInviteRequestForm, self).__init__(*args, **kwargs)
		self.fields['contacts'].queryset = Contact.objects.filter(user=self.user)
		self.fields['invite_type'].widget = forms.HiddenInput()
		self.fields['postcard_background'].update_choices()

	def clean(self):
		if (	not self.cleaned_data.get('contacts', False) and
				not self.cleaned_data.get('providers', False) and
				not self.cleaned_data.get('email_list', False)):
			raise forms.ValidationError('You must add at least one recipient.')
		return self.cleaned_data

class SimpleJoinInviteRequestForm(forms.Form):
	emails = forms.EmailField(label="Email", required=True, widget=forms.TextInput(attrs={'placeholder':'Email address'}))
	message = forms.CharField(label="Message", required=False, widget=forms.Textarea(attrs = {'cols': '40', 'rows': '5'}))
