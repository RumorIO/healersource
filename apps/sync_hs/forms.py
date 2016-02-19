from django import forms
from healers.models import Timezone


class TimezoneForm(forms.Form):
	timezone = forms.ChoiceField(label="My Timezone", choices=Timezone.TIMEZONE_CHOICES)


class UnavailableCalendarsForm(forms.Form):
	calendars = forms.MultipleChoiceField(required=False, label="Use the following Google Calendar(s) to subtract from my HealerSource Availability",
											widget=forms.CheckboxSelectMultiple())

	def __init__(self, *args, **kwargs):
		calendars_choices = kwargs.pop('calendars_choices', [])
		super(UnavailableCalendarsForm, self).__init__(*args, **kwargs)

		self.fields['calendars'].choices = calendars_choices
