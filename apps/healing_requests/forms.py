from django import forms
from django_select2.forms import Select2MultipleWidget
from captcha.fields import CaptchaField

from healers.forms import categories_as_choices
from healers.models import Zipcode
from healers.utils import html_sanitize
from util.widgets import TinyEditor
from healing_requests.models import (HealingRequest, HealingRequestSearch,
	get_speciality_id)
from account_hs.forms import ClientSignupWithLastNameForm


def get_specialities_choices():
	categories = categories_as_choices()
	try:
			for category in categories:
					category = category[1]
					category_id = category[0][0]
					for n in range(1, len(category)):
							category[n][0] = category_id + '_' + category[n][0]

	except IndexError:
		pass

	return categories


class HealingRequestFormBase(forms.ModelForm):
	specialities = forms.MultipleChoiceField(required=False, widget=Select2MultipleWidget(attrs={'closeOnSelect': True, 'data-allow-clear': False}),
		choices=get_specialities_choices())
	speciality_categories = forms.MultipleChoiceField(required=False, widget=forms.MultipleHiddenInput())
	search_specialities = forms.MultipleChoiceField(required=False, widget=Select2MultipleWidget(attrs={'closeOnSelect': True, 'data-allow-clear': False}),
		choices=get_specialities_choices())
	search_city_or_zipcode = forms.CharField(max_length=50, label="City", required=False,
								widget=forms.TextInput(attrs={
									'placeholder': 'City or Town',
									'class': 'search_city_or_zipcode'}))
	zipcode = forms.CharField(required=False, widget=forms.HiddenInput(attrs={
			'class': 'zipcode'
		}))

	accept_location = forms.BooleanField(required=False, initial=False)
	accept_cost_per_session = forms.BooleanField(required=False, initial=False)

	description = forms.CharField(label="Description", widget=TinyEditor())

	def __init__(self, data=None, *args, **kwargs):
		if data is not None:
			data = data.copy()
			near_my_location = data.get('near_my_location', None)
			accept_location = data.get('accept_location', None)
			accept_cost_per_session = data.get('accept_cost_per_session', None)
			if data.get('zipcode', None) and (near_my_location is False or accept_location):
				data['location'] = Zipcode.objects.get(id=data['zipcode']).id
			if not accept_cost_per_session:
				data['cost_per_session'] = None

		super(HealingRequestFormBase, self).__init__(data=data, *args, **kwargs)

		#Set initial values based on instance
		if kwargs.get('instance', None):
			instance = kwargs['instance']
			if instance.location:
				self.initial['zipcode'] = instance.location.id
				self.initial['search_city_or_zipcode'] = "%s, %s" % (
					instance.location.city.capitalize(), instance.location.state.upper())

			if instance.specialities.exists() or instance.speciality_categories.exists():
				specialities_arr = []
				for speciality in instance.specialities.all():
					id = get_speciality_id(speciality.id)
					if id not in specialities_arr:
						specialities_arr.append(id)

				for cat in instance.speciality_categories.all():
					id = 'p:%d' % cat.id
					specialities_arr.append(id)

				self.initial['specialities'] = specialities_arr

			if instance.cost_per_session:
				self.initial['accept_cost_per_session'] = True

		if self.initial.get('show_photo', None) is not True:
			self.initial['show_photo'] = True
		if self.initial.get('show_full_name', None) is not True:
			self.initial['show_full_name'] = True

	def clean_description(self):
		return html_sanitize(self.cleaned_data['description'])

	def clean_zipcode(self):
		zipcode = self.cleaned_data.get('zipcode', None)
		if zipcode and int(zipcode):
			return zipcode

	def clean(self):
		cleaned_data = self.cleaned_data

		if cleaned_data.get('zipcode', None):
			cleaned_data['location'] = Zipcode.objects.get(id=cleaned_data['zipcode'])

		if cleaned_data.get('only_my_specialities', None) is not False:
			cleaned_data['search_specialities'] = []

		if cleaned_data.get('only_my_specialities', None) is None:
			cleaned_data['only_my_specialities'] = False

		if cleaned_data.get('near_my_location', None) is None:
			cleaned_data['near_my_location'] = False

		cleaned_data['speciality_categories'] = []

		return cleaned_data


class HealingRequestForm(HealingRequestFormBase):

	class Meta:
		model = HealingRequest
		exclude = ('user',)


class HealingRequestSearchForm(HealingRequestFormBase):
	description = forms.CharField(label="Description", required=False, widget=TinyEditor())
	only_my_specialities = forms.NullBooleanField(initial=False)
	near_my_location = forms.NullBooleanField(initial=False)

	class Meta:
		model = HealingRequestSearch
		exclude = ('user', 'description')

	def clean(self):
		cleaned_data = super(HealingRequestSearchForm, self).clean()

		if cleaned_data.get('saved', None):
			can_be_saved = False
		else:
			can_be_saved = True

		keys = ['remote_healing', 'trade_for_services']
		for key in keys:
			if cleaned_data.get(key, None):
				can_be_saved = True

		if not can_be_saved and cleaned_data.get('accept_cost_per_session', None) and cleaned_data.get('cost_per_session', None):
			can_be_saved = True

		elif cleaned_data.get('only_my_specialities', None) and not can_be_saved:
			can_be_saved = True

		elif not can_be_saved and cleaned_data.get('only_my_specialities', None) is False and cleaned_data.get('search_specialities', None):
			can_be_saved = True

		elif not can_be_saved and cleaned_data.get('near_my_location', None):
			can_be_saved = True

		elif not can_be_saved and cleaned_data.get('near_my_location', None) is False and cleaned_data.get('zipcode', None):
			can_be_saved = True

		if not can_be_saved:
			cleaned_data['saved'] = False

		return cleaned_data

		'''
		Sample cleaned_data
		{'remote_healing': False, 'only_my_specialities': False,
		'accept_cost_per_session': False, 'search_city_or_zipcode': u'',
		'description': '', 'specialities': [], 'zipcode': u'',
		'cost_per_session': None, 'accept_location': False,
		'search_specialities': [],
		'near_my_location': False, 'saved': True, 'trade_for_services': False}
		'''


class HealingRequestUserFormUnregistered(ClientSignupWithLastNameForm):
	security_verification = CaptchaField(label='Security Verification')
