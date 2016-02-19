from django import forms

from ambassador.models import Plan

COLOR_MAX_LENGTH = 7  # for #aabbcc


class SettingsForm(forms.Form):
	plan = forms.ModelChoiceField(
		label='',
		queryset=Plan.objects.all(),
		widget=forms.RadioSelect,
		empty_label=None,
		required=True,
		error_messages={'required': 'Please select one of the plans.'})

	def __init__(self, *args, **kwargs):
		self.client = kwargs.pop('client')
		super(SettingsForm, self).__init__(*args, **kwargs)

		self.fields['plan'].initial = self.client.ambassador_plan

	def save(self):
		self.client.ambassador_plan = self.cleaned_data['plan']
		self.client.save()


class EmbedSettingsForm(forms.Form):
	"""
	Settings for plugin page
	"""
	search_all = forms.ChoiceField(
		label='',
		widget=forms.RadioSelect,
		required=True)
	background_color = forms.CharField(
		label='Plugin Background Color',
		max_length=COLOR_MAX_LENGTH,
		required=False)

	def __init__(self, *args, **kwargs):
		self.client = kwargs.pop('client')
		super(EmbedSettingsForm, self).__init__(*args, **kwargs)

		if not self.client.is_referrals_group():
			del self.fields['search_all']
		else:
			# TODO: try BooleanField
			# convert bool to '0'|'1'
			self.fields['search_all'].initial = str(int(self.client.embed_search_all))
			self.fields['search_all'].choices = (
				('1', 'Show all HealerSource Providers.'),
				('0', 'Show only providers at {}'.format(self.client)))

		self.fields['background_color'].initial = self.client.embed_background_color

	def clean_background_color(self):
		color = self.cleaned_data['background_color']
		if len(color) and len(color) < COLOR_MAX_LENGTH and not color.startswith('#'):
			color = '#' + color.lower()
		return color

	def save(self):
		if 'search_all' in self.cleaned_data:
			self.client.embed_search_all = self.cleaned_data['search_all'] == '1'
		self.client.embed_background_color = self.cleaned_data['background_color']
		self.client.save()
