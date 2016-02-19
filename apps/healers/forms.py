from datetime import datetime, timedelta, time
from collections import defaultdict

from django.conf import settings
from django import forms
from django.forms.widgets import Widget, Select, MultipleHiddenInput
from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from pinax.apps.account.forms import ResetPasswordKeyForm
from emailconfirmation.models import EmailAddress
from captcha.fields import CaptchaField
from django_select2.forms import Select2Widget

from account_hs.forms import ClientSignupWithLastNameForm, LoginFormHS
from account_hs.utils import after_signup
from clients.models import Client, ClientLocation
from clients.forms import (ClientForm, AboutClientForm,
	ClientLocationForm)
from modality.models import Modality, ModalityCategory
from healers.models import (Healer, Location, Clients, TreatmentType,
	TreatmentTypeLength, Timezone, Zipcode, Room, is_healer, is_wellness_center,
	DiscountCode)
from healers.utils import (send_hs_mail,
	reset_center_and_providers_availabilities, save_phone_number)
from django.db.models.query_utils import Q

class HealerOptionalInfoForm(ClientForm):
#	phonesVisibility = forms.ChoiceField(label="Phone Numbers Visibility", choices=Healer.PROFILE_VISIBILITY_CHOICES)
	years_in_practice = forms.CharField(max_length=4, required=False, label=u'Years In Practice', widget=forms.TextInput(attrs={'size' : '4'}))

	website = forms.CharField(max_length=255, required=False, label=u'Your Website', widget=forms.TextInput(attrs={'size' : '56'}))
	facebook = forms.CharField(max_length=255, required=False, label=u'Facebook', widget=forms.TextInput(attrs={'size' : '56'}))
	twitter = forms.CharField(max_length=255, required=False, label=u'Twitter', widget=forms.TextInput(attrs={'size' : '56'}))
	google_plus = forms.CharField(max_length=255, required=False, label=u'Google+', widget=forms.TextInput(attrs={'size' : '56'}))
	linkedin = forms.CharField(max_length=255, required=False, label=u'LinkedIn', widget=forms.TextInput(attrs={'size' : '56'}))
	yelp = forms.CharField(max_length=255, required=False, label=u'Yelp', widget=forms.TextInput(attrs={'size' : '56'}))
	profile_completeness_reminder_interval = forms.ChoiceField(required=False, choices=Healer.PROFILE_REMINDER_INTERVAL_CHOICES)


class HealerForm(HealerOptionalInfoForm):
	def __init__(self, *args, **kwargs):
		super(HealerForm, self).__init__(*args, **kwargs)
		self.fields['send_reminders'].label = "Send me a Reminder the day before for Appointments I'm Receiving"

	profileVisibility = forms.ChoiceField(label="Profile Visibility", choices=Healer.PROFILE_VISIBILITY_CHOICES)
	client_screening = forms.ChoiceField(label="Client Screening", choices=Healer.CLIENT_SCREENING_CHOICES)
	timezone = forms.ChoiceField(label="My Timezone", choices=(('','------------'),)+Timezone.TIMEZONE_CHOICES)
	location_bar_title = forms.CharField(max_length=36, required=False, label=u'Location Bar Title', widget=forms.TextInput(attrs={'size' : '24'}) )


class CreateProviderForm(AboutClientForm):
	first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
	last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
	email = forms.EmailField(label=u'Email', required=True, widget=forms.TextInput(attrs={'size': '18'}))
	phone = forms.CharField(required=False, label="Phone Number", max_length=30, widget=forms.TextInput(attrs={'size': '18'}))
	years_in_practice = forms.CharField(max_length=4, required=False, label=u'Years In Practice', widget=forms.TextInput(attrs={'size': '4'}))
	modalities = forms.ModelMultipleChoiceField(queryset=Modality.objects_approved.all(), required=False, widget=forms.MultipleHiddenInput())


class ProviderConfirmForm(ResetPasswordKeyForm):
	def save(self):
		super(ProviderConfirmForm, self).save()
		EmailAddress.objects.filter(user=self.user).update(verified=True)
		self.user.is_active = True
		self.user.save()
		after_signup(self.user, account_type='healer', email_confirmed=True)


class WellnessCenterOptionalInfoForm(HealerOptionalInfoForm):
	def __init__(self, *args, **kwargs):
		super(WellnessCenterOptionalInfoForm, self).__init__(*args, **kwargs)
		del self.fields['last_name']


class WellnessCenterForm(HealerForm):
	def __init__(self, *args, **kwargs):
		super(WellnessCenterForm, self).__init__(*args, **kwargs)
		del self.fields['last_name']

class ScheduleSettingsForm(forms.Form):

	bookAheadDays = forms.IntegerField(label="Maximum Days From Now That a Client Can Book an Appointment", min_value=1, max_value=365,
											widget=forms.TextInput(attrs={'size' : '2'}))
	leadTime = forms.IntegerField(label="Minimum Advance Notice for Bookings", min_value=0, max_value=720, widget=forms.TextInput(attrs={'size' : '2'}))
	setup_time = forms.IntegerField(label="Setup Time Between Appointments", min_value=0, max_value=600, widget=forms.TextInput(attrs={'size' : '2'}))
	manualAppointmentConfirmation = forms.ChoiceField(label="Appointment Confirmation", choices=Healer.CONFIRMATION_CHOICES)
	intakeFormBooking = forms.ChoiceField(label="Intake Form", choices=Healer.INTAKE_FORM_BOOKING_CHOICES)
	booking_optional_message_allowed = forms.BooleanField(label='Allow user to enter an optional message to you when booking', required=False)
#	scheduleVisibility = forms.ChoiceField(label="Schedule Visibility", choices=Healer.SCHEDULE_VISIBILITY_CHOICES)

	office_hours_start = forms.TimeField(widget=forms.TimeInput(attrs={'class' : 'timepicker office_hours', 'size' : '7'}, format="%I:%M%p"), input_formats=["%I:%M%p"])
	office_hours_end = forms.TimeField(widget=forms.TimeInput(attrs={'class' : 'timepicker office_hours', 'size' : '7'}, format="%I:%M%p"), input_formats=["%I:%M%p"])

	cancellation_policy = forms.CharField(label="Cancellation Policy", required=False, widget=forms.Textarea(attrs={'cols': '70', 'rows': '3', 'style': 'vertical-align: top;'}))
	additional_text_for_email = forms.CharField(label="Additional Text to be added to Appointment Confirmation Emails", required=False, widget=forms.Textarea(attrs={'cols': '70', 'rows': '3', 'style': 'vertical-align: top;'}))

	send_sms_appt_request = forms.BooleanField(required=False)
	phone = forms.CharField(required=False, label="Phone Number", max_length=30, widget=forms.TextInput(attrs={'size': '18'}))
	common_availability = forms.ChoiceField(required=False, widget=forms.RadioSelect,
		choices=((False, 'Each Provider sets their own Availability',),
			(True, 'Use the same Availability for All Providers at our center',)))

	def clean(self):
		start = self.cleaned_data.get('office_hours_start')
		end = self.cleaned_data.get('office_hours_end')

		if start and end:
			if start > end:
				raise forms.ValidationError("Office Hours End Must Be After Start")

		return self.cleaned_data

	@classmethod
	def create(cls, request, healer):
		center = is_wellness_center(healer)
		if request.method == 'POST':
			form = ScheduleSettingsForm(request.POST)
			if form.is_valid():
				healer.leadTime = form.cleaned_data['leadTime']
				healer.manualAppointmentConfirmation = form.cleaned_data['manualAppointmentConfirmation']
				healer.intakeFormBooking = form.cleaned_data['intakeFormBooking']
				healer.booking_optional_message_allowed = form.cleaned_data['booking_optional_message_allowed']
#				healer.scheduleVisibility = int(form.cleaned_data['scheduleVisibility'])
				healer.setup_time = form.cleaned_data['setup_time']
				healer.bookAheadDays = form.cleaned_data['bookAheadDays']
				healer.office_hours_start = form.cleaned_data['office_hours_start']
				healer.office_hours_end = form.cleaned_data['office_hours_end']
				healer.cancellation_policy = form.cleaned_data['cancellation_policy']
				healer.additional_text_for_email = form.cleaned_data['additional_text_for_email']
				healer.send_sms_appt_request = form.cleaned_data['send_sms_appt_request']
				save_phone_number(healer, form.cleaned_data['phone'])

				if str(healer.office_hours_end) == '00:00:00':
					healer.office_hours_end = time(23, 59)

				if center:
					common_availability = form.cleaned_data['common_availability'] == 'True'
					if center.common_availability != common_availability:
						reset_center_and_providers_availabilities(center)
						center.common_availability = common_availability
						center.save()

				healer.save()
		else:
			initial_data = {
				"bookAheadDays": healer.bookAheadDays,
				"leadTime": healer.leadTime,
				"manualAppointmentConfirmation": healer.manualAppointmentConfirmation,
				"intakeFormBooking": healer.intakeFormBooking,
				"booking_optional_message_allowed": healer.booking_optional_message_allowed,
#				"scheduleVisibility": healer.scheduleVisibility,
				"setup_time": healer.setup_time,
				"office_hours_start": healer.office_hours_start,
				"office_hours_end": healer.office_hours_end,
				"cancellation_policy": healer.cancellation_policy,
				"additional_text_for_email": healer.additional_text_for_email,
				"send_sms_appt_request": healer.send_sms_appt_request,
				'phone': healer.first_phone()}
			if center:
				initial_data['common_availability'] = center.common_availability
			form = ScheduleSettingsForm(initial=initial_data)
		return form


class NewUserForm(forms.Form):
	first_name = forms.CharField(
		max_length=30,
		label=u'First Name',
		widget=forms.TextInput(attrs={'size' : '56'})
	)
	last_name = forms.CharField(
		max_length=30,
		required=False,
		label=u'Last Name',
		widget=forms.TextInput(attrs={'size' : '56'})
	)
	phone = forms.CharField(
		max_length=30,
		required=False,
		label=u'Phone Number',
		widget=forms.TextInput(attrs={'size' : '56'})
	)
	email = forms.EmailField(
		label=u'Email',
		required=False,
		widget=forms.TextInput(attrs={'size' : '18'}),
	   help_text="An invitation will be sent to this email"
	)
	send_intake_form = forms.BooleanField(required=False)
	address_line1 = forms.CharField(max_length=42, required=False, label='Address Line 1', widget=forms.TextInput(attrs={'size': '42'}))
	address_line2 = forms.CharField(max_length=42, required=False, label='Address Line 2', widget=forms.TextInput(attrs={'size': '42'}))
	postal_code = forms.CharField(max_length=10, required=False, label='Zip Code', widget=forms.TextInput(attrs={'size': '10'}))
	city = forms.CharField(max_length=42, required=False, widget=forms.TextInput(attrs={'size': '42'}))
	state_province = forms.CharField(max_length=42, required=False, label='State', widget=forms.TextInput(attrs={'size': '42'}))
	country = forms.CharField(max_length=42, required=False, label='Country', widget=forms.TextInput(attrs={'size': '42'}))

class NewUserFormUnregistered(ClientSignupWithLastNameForm):
	phone = forms.CharField(max_length=30, label=u'Phone Number', widget=forms.TextInput(attrs={'size' : '56'}) )
	note = forms.CharField(label="Optional Message",
		required=False,
		widget=forms.Textarea(attrs = {'cols': '40', 'rows': '5'}))

	security_verification = CaptchaField(label='Security Verification')

	def __init__(self, *args, **kwargs):
		super(NewUserFormUnregistered, self).__init__(*args, **kwargs)

#class NewUserFormUnregistered(forms.Form):
#	first_name = forms.CharField(max_length=30, label=u'First Name', widget=forms.TextInput(attrs={'size' : '56'}) )
#	last_name = forms.CharField(max_length=30, label=u'Last Name', widget=forms.TextInput(attrs={'size' : '56'}) )
#	phone = forms.CharField(max_length=30, required=False, label=u'Phone Number', widget=forms.TextInput(attrs={'size' : '56'}) )
#	email = forms.EmailField(label=u'Email', widget=forms.TextInput(attrs={'size' : '18'}) )
#	referred_by = forms.CharField(label="Who referred you?", required=False)
#	note = forms.CharField(label="Optional Message",
#		required=False,
#		widget=forms.Textarea(attrs = {'cols': '40', 'rows': '5'}))

class BookingLoginForm(LoginFormHS):

	def __init__(self, *args, **kwargs):
		super(BookingLoginForm, self).__init__(*args, **kwargs)
		self.fields['email'].widget = forms.TextInput()
		self.fields['password'].widget = forms.PasswordInput()
		self.fields['remember'].widget = forms.HiddenInput()
		self.fields['note'] = forms.CharField(required=False, widget=forms.HiddenInput())

class SplitDateTimePickerWidget(forms.widgets.SplitDateTimeWidget):
	def __init__(self, attrs=None, date_format=None, time_format=None):
		attrs_date = {'class' : 'datepicker', 'size' : '10'}
		attrs_time = {'class' : 'timepicker', 'size' : '7'}
		widgets = (forms.DateInput(attrs=attrs_date, format="%m/%d/%Y"),
						 forms.TimeInput(attrs=attrs_time, format="%I:%M%p"))
		super(forms.widgets.SplitDateTimeWidget, self).__init__(widgets, attrs)

class VacationForm(forms.Form):
	start = forms.SplitDateTimeField(label="Start", widget=SplitDateTimePickerWidget(), input_time_formats=["%I:%M%p"])
	end = forms.SplitDateTimeField(label="End", widget=SplitDateTimePickerWidget(), input_time_formats=["%I:%M%p"])

	def clean(self):
		cleaned_data = self.cleaned_data
		start = cleaned_data.get('start')
		end = cleaned_data.get('end')

		if start and end:
			if start > end:
				raise forms.ValidationError("End Must Be After Start")
		else:
			raise forms.ValidationError("Both start and end are needed")

		return self.cleaned_data

class ColorSelect(Widget):
	"""
		Widget to show color choices as boxes.
	"""
	def __init__(self, attrs=None, choices=()):
		super(ColorSelect, self).__init__(attrs)
		self.choices = list(choices)

	def render(self, name, value, attrs=None, choices=()):
		final_attrs = self.build_attrs(attrs, name=name)
		selected_color = self.choices[0][0] if not value else value
		output = [u'<input type="hidden" value="%s" %s/>' % (selected_color, flatatt(final_attrs))]
		for color in self.choices:
			context = {
				'STATIC_URL': settings.STATIC_URL,
				'color': color[0],
				'color_classes': 'color_box_selected' if selected_color == color[0] else ''
			}
			color_box = render_to_string('healers/color_box.html', context)
			output.append(color_box)
		return mark_safe(u'\n'.join(output))

	class Media:
		js = (settings.STATIC_URL + 'healersource/js/color_select.js',)


class LocationForm(ClientLocationForm):
	def __init__(self, *args, **kwargs):
		self.healer = kwargs.pop('healer', False)
		account_setup = kwargs.pop('account_setup', False)
		if self.healer:
			self.schedule_is_visible = self.healer.scheduleVisibility != Healer.VISIBLE_DISABLED
		self.is_wellness_center = is_wellness_center(self.healer)
		super(LocationForm, self).__init__(*args, **kwargs)
		choices = self.fields['color'].widget.choices
		if self.is_wellness_center:
			choices = reversed(choices)
		self.fields['color'].widget = ColorSelect()
		self.fields['color'].widget.choices = choices
		self.fields['title'].widget = forms.TextInput(attrs={'required': ''})
		if (not account_setup and self.schedule_is_visible and not
				self.is_wellness_center):
			self.fields['color'].required = True
			if not self.instance.pk:
				self.fields['color'].initial = self.get_next_color()
		else:
			del self.fields['color']
			#del self.fields['book_online']

	def get_next_color(self):
		position = ClientLocation.objects.filter(client=self.healer).count()
		return Location.get_next_color(position, self.is_wellness_center)

	class Meta:
		model = Location
		fields = ('title', 'addressVisibility', 'address_line1', 'address_line2',
					'city', 'state_province', 'postal_code', 'country', 'color',
					'book_online')
		widgets = {
			'book_online': forms.RadioSelect()
		}

	def save(self, **kwargs):
		location = super(LocationForm, self).save(commit=False)
		if not location.pk and not self.schedule_is_visible:
			location.color = self.get_next_color()
		location.save()
		return location

	def clean_title(self):
		return self.cleaned_data['title'].strip()


class SelectMinutesWidget(Widget):
	"""
		A Widget that splits minutes input into two <select> boxes - hours, minutes.
	"""
	hour_field = '%s_hour'
	minute_field = '%s_minute'

	def __init__(self, attrs=None, required=True):
		self.attrs = attrs or {}
		self.required = required
		self.hours = range(0, 24)
		self.minutes = range(0, 60, 5)

	def render(self, name, value, attrs=None):
		if value:
			hour_val, minute_val = divmod(value, 60)
		else:
			hour_val = minute_val = 0

		choices = [(i, i) for i in self.hours]
		hour_html = self.create_select(name, self.hour_field, hour_val, choices)
		choices = [(i, i) for i in self.minutes]
		minute_html = self.create_select(name, self.minute_field, minute_val, choices)

		output = "%s hours %s min" % (hour_html, minute_html)
		return mark_safe(output)

	def id_for_label(self, id_):
		return '%s_hour' % id_
	id_for_label = classmethod(id_for_label)

	def value_from_datadict(self, data, files, name):
		h = data.get(self.hour_field % name)
		m = data.get(self.minute_field % name)
		if h and m:
			return int(h)*60 + int(m)
		return data.get(name, None)

	def create_select(self, name, field, val, choices):
		if 'id' in self.attrs:
			id_ = self.attrs['id']
		else:
			id_ = 'id_%s' % name
		local_attrs = self.build_attrs(id=field % id_)
		s = Select(choices=choices)
		select_html = s.render(field % name, val, local_attrs)
		return select_html

	class Media:
		js = (settings.STATIC_URL + 'healersource/js/select_minutes.js',)


class RoomForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(RoomForm, self).__init__(*args, **kwargs)
		self.fields['name'].label = 'Room Name'
		self.fields['name'].widget = forms.TextInput(attrs={'required': ''})

	class Meta:
		model = Room
		fields = ('name', )


class TreatmentTypeLengthForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(TreatmentTypeLengthForm, self).__init__(*args, **kwargs)
		self.fields['length'] = forms.IntegerField(widget=SelectMinutesWidget(), min_value=5)
		self.fields['cost'].widget = forms.TextInput(attrs={'size': '2',
			'required': ''})

	class Meta:
		model = TreatmentTypeLength
		fields = ('length', 'cost')


class RoomsSelect(MultipleHiddenInput):
	def __init__(self, available_locations, attrs=None, choices=()):
		super(RoomsSelect, self).__init__(attrs)
		self.choices = list(choices)
		self.available_locations = available_locations

	def render(self, name, value, attrs=None, choices=()):
		choices = defaultdict(list)
		for choice in self.choices:
			room_id = choice[0]
			room = choice[1]
			location = Room.objects.get(pk=choice[0]).location
			if self.available_locations is not None:
				if location.id not in self.available_locations:
					continue
			choices[location.title].append((room_id, room))

		final_attrs = self.build_attrs(attrs, name=name)
		output = render_to_string('healers/room_select.html', {
			'original_choices': self.choices,
			'choices': dict(choices),
			'values': value,
			'attrs': flatatt(final_attrs)})
		return mark_safe(output)

	class Media:
		js = (settings.STATIC_URL + 'healersource/js/room_select.js',)


class NumberInput(forms.TextInput):
	input_type = 'number'


class DiscountCodeForm(forms.ModelForm):
	CODE_PATTERN_RULE = 'Code may contain only alphabetic characters and digits.'

	def __init__(self, *args, **kwargs):
		self.healer = kwargs.pop('healer', None)
		super(DiscountCodeForm, self).__init__(*args, **kwargs)
		self.fields['code'].widget = forms.TextInput(attrs={'required': '',
			'maxlength': 30, 'pattern': '[0-9A-Za-z]+', 'title': DiscountCodeForm.CODE_PATTERN_RULE})
		self.fields['amount'].widget = NumberInput(attrs={'required': '', 'min': 1, 'max': 1000})

	class Meta:
		model = DiscountCode
		fields = ('code', 'amount', 'type')

	class Media:
		js = (settings.STATIC_URL + 'healersource/js/discount_codes.js',)

	def clean_code(self):
		code = self.cleaned_data['code']
		if not code.isalnum():
			raise forms.ValidationError(DiscountCodeForm.CODE_PATTERN_RULE)
		return code.upper()

	def clean(self):
		def validate_unique_code():
			healer = self.healer
			if healer is None:
				healer = self.instance.healer
			codes = DiscountCode.objects.filter(healer=healer, code=data['code'])
			if self.instance.pk is not None:
				codes = codes.exclude(pk=self.instance.pk)
			if codes.exists():
				raise forms.ValidationError('Code with this name already exists.')

		super(DiscountCodeForm, self).clean()
		data = self.cleaned_data
		if 'code' in data:
			validate_unique_code()
		if data['type'] == '%':
			if data['amount'] > 100:
				raise forms.ValidationError('Amount value has to be less or equal to 100%.')
		return data

	def save(self):
		discount_code = super(DiscountCodeForm, self).save(commit=False)
		if self.healer is not None:
			discount_code.healer = self.healer
		discount_code.save()
		return discount_code


class TreatmentTypeForm(forms.ModelForm):
	def __init__(self, available_locations=None, *args, **kwargs):
		super(TreatmentTypeForm, self).__init__(*args, **kwargs)
		self.fields['title'].label = 'Treatment Name'
		self.fields['title'].widget = forms.TextInput(attrs={'size': '33', 'required': ''})
		self.fields['description'].widget = forms.Textarea(attrs={'rows': '8',
			'style': 'width: 95%'})
		self.fields['rooms'].widget = RoomsSelect(choices=self.fields['rooms'].choices, available_locations=available_locations)
		self.fields['rooms'].help_text = None

	class Meta:
		model = TreatmentType
		fields = ('title', 'description', 'rooms')

	def clean_title(self):
		return self.cleaned_data['title'].strip()


class TreatmentTypeLengthChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, length):
		return length.full_title()


class NewAppointmentForm(forms.Form):
#	healer = None

	def __init__(self, user, data=None):
		self.healer = None
		now = settings.GET_NOW()
		if is_healer(user):
			self.healer = user.client.healer
			now = self.healer.get_local_time()

		users = Clients.objects.friends_for_user(user)
		clients = [(u["friend"].client.id, str(u["friend"].client)) for u in users]
		self.base_fields['client'].choices = clients
		self.base_fields['client'].widget.choices = clients

		healer_locations = ClientLocation.objects.filter(client__user=user)
		locations = [(hl.location.id, str(hl.location)) for hl in healer_locations]

		if len(locations) == 0:
			locations.insert(0, ("-1", Location.get_name(None)))

		self.base_fields['location'].choices = locations
		self.base_fields['location'].widget.choices = locations

		time_choices = []
		dt = now.replace(hour=0, minute=0)
		dt_end = dt + timedelta(days=1)
		while dt < dt_end:
			time_choices.append((dt.strftime("%H:%M"), dt.strftime("%I:%M %p").lower()))
			dt += timedelta(minutes=15)

#		self.base_fields['start'].choices = time_choices
#		self.base_fields['end'].choices = time_choices

		self.base_fields['start'].widget.choices = time_choices

		self.base_fields['treatment_length'].queryset = TreatmentTypeLength.objects.filter(treatment_type__healer__user=user)

#		self.base_fields['start'].widget.initial = ["12:00"]
#		self.base_fields['end'].widget.initial = [12]

		super(forms.Form, self).__init__(initial={'start': '12:00', 'end': '13:00', 'date': dt.date()+timedelta(days=1)}, data=data)

	client = forms.ChoiceField(label="Client", choices=())
	location = forms.ChoiceField(label="Location", choices=())
	date = forms.DateField(label="Date", widget=forms.DateInput(attrs={'class': 'datepicker', 'size': '10'}, format="%m/%d/%Y"))
	start = forms.TimeField(label="Start", widget=forms.Select())
	treatment_length = TreatmentTypeLengthChoiceField(label="Treatment", empty_label=None, queryset=None)

	def get_start_and_end_dates(self):
		date = self.cleaned_data.get('date')
		start_time = self.cleaned_data.get('start')
		treatment = self.cleaned_data.get('treatment_length')

		if date and start_time and treatment:
			start = datetime(date.year, date.month, date.day, start_time.hour, start_time.minute, 0)
			end = start + timedelta(minutes=treatment.length)
			return start, end
		else:
			return None, None

	def clean(self):
		now = settings.GET_NOW()
		if self.healer:
			now = self.healer.get_local_time()
		start, end = self.get_start_and_end_dates()

		if start and end:
			if start > end:
				raise forms.ValidationError("End Must Be After Start")

			if end < now:
				raise forms.ValidationError("You cant make appointments in the past")

#			conflicting_appts = Appointment.objects.filter(healer=self.cleaned_data.get("h"), start__week_day = fix_weekday(self.start.weekday()) )

		else:
			raise forms.ValidationError("Both start and end and date are needed")

		return self.cleaned_data


class ClientsSearchForm(forms.Form):
	query = forms.CharField(max_length=75, widget=forms.TextInput(attrs={'size': 25,
																		 'maxlength': 75,
																		 'placeholder': 'Name or Email Address'}))

	def __init__(self, *args, **kwargs):
		self.search_type = kwargs.pop('search_type', None)
		super(ClientsSearchForm,self).__init__(*args, **kwargs)
		if self.search_type == 'clients':
			self.fields['query'].label = 'Search All Clients'
		else:
			self.fields['query'].label = 'Search All Providers'

	def clean_query(self):
		query = self.cleaned_data['query'].strip()
		if not len(query):
			raise forms.ValidationError("Empty search query.")
		return query

	def search(self, my_client_id=None):
		query = self.cleaned_data['query']
		if self.search_type == 'clients':
			model = Client
		else:
			model = Healer

		qs = model.objects.all()

		clients = ClientsSearchForm.search_by_name_or_email(qs, query)
		return clients

	@classmethod
	def search_by_name_or_email(cls, qs, name_or_email, search_all=False):
		if not search_all:
			qs = qs.exclude(Q(user__is_active=False))
		qs = qs.order_by("-user__first_name")

		if name_or_email.find('@') != -1:
			clients = qs.filter(Q(user__email=name_or_email))
		else:
			names = name_or_email.split()
			if len(names) == 1:
				clients = qs.filter(Q(user__first_name__icontains=name_or_email) |
												Q(user__last_name__icontains=name_or_email) | Q(user__username__icontains=name_or_email))

			else:
				clients = qs.filter(user__first_name__icontains=names[0]).filter(user__last_name__icontains=names[-1])

		return clients

#class ClientsIpSearchForm(ClientsSearchForm):
#
#	def search(self, my_client_id=None):
#		ip = self.cleaned_data['query']
#
#		geoip = GeoIP()
#		pnt = geoip.geos(ip)
#		if not pnt:
#			return []
#		zipcodes = Zipcode.objects.values_list('code', flat=True).filter(point__distance_lte=(pnt, D(mi=50)))
#
#		if self.search_type == 'clients':
#			model = Client
#		else:
#			model = Healer
#		clients = model.objects.filter(clientlocation__location__postal_code__in=zipcodes)
#		clients = clients.exclude(Q(user__is_active=False) | Q(approval_rating=0) | Q(id=my_client_id)).order_by("-user__first_name")
#
#		return clients


def categories_as_choices():
	categories = []

	healers_complete = Healer.complete.values_list('pk', flat=True)

	# Modality Category
	for category in ModalityCategory.objects.order_by('title'):
		new_category = []
		sub_categories = []

		# Modalities
		ptr = 0
		for sub_category in category.modality_set.filter(healer__pk__in=healers_complete, approved=True).\
			distinct().order_by('title'):

			#Selecteable parent
			if ptr == 0:
				parent_id = 'p:' + str(category.id)
				parent_title = 'Any type of ' + category.title
				sub_categories.append([parent_id, parent_title])
				ptr = 1

			child_id = 'c:' + str(sub_category.id)
			sub_categories.append([child_id, sub_category.title])

		new_category = [category.title, sub_categories]
		categories.append(new_category)

	return categories


class HealerSearchForm(forms.Form):
	'''
	modality = forms.CharField(max_length=50, label="Type", required=False,
							   widget=forms.TextInput(attrs={
									'placeholder': 'Specialty (optional)',
									'id': 'healer_modality_input',
									'class': 'modality_input'
							   }))

	'''
	search_city_or_zipcode = forms.CharField(max_length=50, label="City", required=False,
								widget=forms.TextInput(attrs={
									'placeholder': 'City or Town',
									'class': 'search_city_or_zipcode'}))
	zipcode = forms.CharField(required=False,
		widget=forms.HiddenInput(attrs={'class': 'zipcode'}))
	city = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())
	state = forms.CharField(max_length=2, required=False, widget=forms.HiddenInput())

	modality_id = forms.IntegerField(required=False, widget=forms.HiddenInput(attrs={'id':'modality_id_hidden'}))
	modality_category_id = forms.IntegerField(required=False, widget=forms.HiddenInput(attrs={'id':'modality_category_id_hidden'}))

	name_or_email = forms.CharField(required=False, max_length=75, label="Provider Name",
									widget=forms.TextInput(
										attrs={'size': 25,
											   'maxlength': 75,
											   'placeholder': 'Provider Name or Email'
#												'id': ''
										}))

	modality2 = forms.ChoiceField(required=False, widget=Select2Widget(attrs={'data-placeholder': 'Any Specialty'}),
		#[ ('', 'Any Specialty') ] +
		choices=categories_as_choices())

	modality3 = forms.ChoiceField(required=False, widget=Select2Widget(attrs={'data-placeholder': 'Any Specialty'}),
		#[ ('', 'Any Specialty') ] +
		choices=categories_as_choices())

	order_by_top = forms.BooleanField(
		required=False, widget=forms.HiddenInput())

	def __init__(self, *args, **kwargs):
		self.city_or_zipcode_placeholder = kwargs.pop(
			'city_or_zipcode_placeholder', 'City')
		super(HealerSearchForm, self).__init__(*args, **kwargs)

	def get_zipcode(self):
		if self.cleaned_data.get('city', False):
			try:
				return Zipcode.objects.filter(
					city=self.cleaned_data['city'].upper(),
					state=self.cleaned_data['state']
				)[:1][0]
			except (Zipcode.DoesNotExist, IndexError):
				return
		elif self.cleaned_data.get('zipcode', False):
			try:
				return Zipcode.objects.get(code=self.cleaned_data['zipcode'])
			except Zipcode.DoesNotExist:
				return


class ConciergeForm(forms.Form):
	name = forms.CharField(
		max_length=30,
		widget=forms.TextInput(attrs={'size': '56', 'placeholder': 'Your Name', 'required': 'required'})
	)
	phone = forms.CharField(
		max_length=30,
		required=False,
		widget=forms.TextInput(attrs={'size': '56', 'placeholder': 'Phone Number'})
	)
	email = forms.EmailField(
		required=False,
		widget=forms.TextInput(attrs={'size': '18', 'placeholder': 'Email'})
	)

	def clean(self):
		cleaned_data = super(ConciergeForm, self).clean()
		if not (cleaned_data.get('email', False) or cleaned_data.get('phone', False)):
			raise forms.ValidationError('Enter either phone number or email')

	def email_data(self, user):
		send_hs_mail('New concierge request',
			"healers/emails/concierge.txt",
			self.data, settings.DEFAULT_FROM_EMAIL, [user.email])


class GiftCertificatesSettingForm(forms.Form):
	gift_certificates = forms.BooleanField(required=False,
		label='Enable Gift Certificates')
	gift_certificates_expiration_period = forms.IntegerField(
		widget=forms.TextInput(attrs={'size': '4', 'type': 'number'}))
	gift_certificates_expiration_period_type = forms.ChoiceField(
		choices=Healer.GIFT_CERTIFICATES_EXPIRATION_PERIOD_TYPE_CHOICES)


class GiftCertificatesPurchaseUnregFormContent(forms.Form):
	purchased_by = forms.CharField(label='From: (your name)', max_length=100,
		widget=forms.TextInput(attrs={'required': 'required'}))
	purchased_by_email = forms.EmailField(label='From (your email)',
		widget=forms.TextInput(attrs={'required': 'required', 'type': 'email'}))


class GiftCertificatesPurchaseForm(forms.Form):
	purchased_for = forms.CharField(label='Recipient Name', max_length=100,
		widget=forms.TextInput(attrs={'required': 'required'}))
	amount = forms.IntegerField(min_value=1, max_value=999,
		widget=forms.TextInput(attrs={'type': 'number',
			'min': 1, 'max': 999, 'required': 'required'}),
		label='Amount')
	message = forms.CharField(label='Message', required=False, widget=forms.Textarea(attrs={'rows': '3'}))
	card_token = forms.CharField(widget=forms.HiddenInput(), required=False)


class GiftCertificatesPurchaseUnregForm(GiftCertificatesPurchaseForm, GiftCertificatesPurchaseUnregFormContent):
	pass
