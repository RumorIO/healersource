import HTMLParser
from bs4 import BeautifulSoup

from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from util.widgets import TinyEditor
from healers.forms import SplitDateTimePickerWidget
from healers.utils import html_sanitize
from events.models import Event, EventLocationDate, EventType


class EventLocationDateForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		def get_choices():
			choices = [(location.pk, unicode(location))
				for location in client.get_locations_objects()]
			choices.append(('new_location', 'New Location -----'))
			return choices
		client = kwargs.pop('client')
		super(EventLocationDateForm, self).__init__(*args, **kwargs)
		self.fields['location'].widget.choices = get_choices()
		self.fields['location'].widget.attrs = {'required': ''}
		self.fields['start'].input_formats = ['%m/%d/%Y %I:%M%p']
		self.fields['end'].input_formats = ['%m/%d/%Y %I:%M%p']

	class Meta:
		model = EventLocationDate
		fields = ('location', 'start', 'end')
		widgets = {
			'start': SplitDateTimePickerWidget(),
			'end': SplitDateTimePickerWidget(),
		}

	class Media:
		js = (settings.STATIC_URL + 'healersource/js/event_location_date_form.js',)

	def clean(self):
		if self.cleaned_data['end'] <= self.cleaned_data['start']:
			raise forms.ValidationError(u'Please make sure Start Date is before End Date.')
		return self.cleaned_data


class EventClearableFileInput(forms.widgets.ClearableFileInput):
	clear_checkbox_label = 'Remove Photo'

	def render(self, name, value, attrs=None):
		substitutions = {
			'initial_text': self.initial_text,
			'input_text': self.input_text,
			'clear_template': '',
			'clear_checkbox_label': self.clear_checkbox_label,
		}
		template = '%(input)s'
		substitutions['input'] = super(EventClearableFileInput, self).render(name, value, attrs)

		if value and hasattr(value, "url"):
			template = '%(initial)s%(input)s'
			substitutions['initial'] = format_html('<div id="event_photo"><img src="{0}" width="100" height="100" /></div>',
				value.url)

		return mark_safe(template % substitutions)


class EventForm(forms.ModelForm):
	class Meta:
		model = Event
		fields = ('title', 'description', 'type', 'photo')
		widgets = {
			'title': forms.TextInput(attrs={'required': ''}),
			'type': forms.Select(attrs={'required': ''}),
			'description': TinyEditor(no_width=True),
			'photo': EventClearableFileInput(),
		}

	def clean_description(self):
		try:
			description = html_sanitize(self.cleaned_data['description'])
		except:
			description = html_sanitize(self.cleaned_data['description'].encode('utf-8'))

		if BeautifulSoup(description).get_text().strip():
			return HTMLParser.HTMLParser().unescape(description.decode('utf-8', 'ignore'))
		else:
			raise forms.ValidationError(u"Description can't be empty.")


class EventsFilterForm(forms.Form):
	def __init__(self, *args, **kwargs):
		def get_choices(objects):
			return [('', '-' * 8)] + [(o.pk, unicode(o)) for o in objects]

		super(EventsFilterForm, self).__init__(*args, **kwargs)
		self.fields['type'].choices = get_choices(EventType.objects.all())

	type = forms.ChoiceField(required=False)
	text = forms.CharField(required=False)
