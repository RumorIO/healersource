from django import forms
from dashboard.models import HealerSettings


class HealerSettingsForm(forms.ModelForm):
	class Meta:
		model = HealerSettings
		fields = ['value', 'description']
