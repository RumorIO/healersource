from bs4 import BeautifulSoup
from django import forms
from django.conf import settings
from healers.utils import html_sanitize
from modality.models import Modality, ModalityCategory
from util.widgets import TinyEditor
from healers.utils import send_queued_mail


class ModalityForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		if 'added_by' in kwargs:
			self.added_by = kwargs.pop('added_by')
		super(ModalityForm, self).__init__(*args, **kwargs)
		self.fields['title'].label = 'Specialty Name'
		self.fields['title'].required = True
		self.fields['title'].widget = forms.TextInput(attrs={'size' : '36'})
		self.fields['description'].required = True
		# self.fields['description'].validators=[MinLengthValidator(300)]
		self.fields['description'].widget=TinyEditor()
		self.fields['category'] = forms.ModelChoiceField(
			queryset=ModalityCategory.objects.all(),
			empty_label=None)

	def save(self, **kwargs):
		modality = super(ModalityForm, self).save(commit=False)
		modality.added_by = self.added_by
		modality.approved = False
		modality.save()

		modality.category.add(self.cleaned_data['category'])

		if self.added_by.modality_set.count() < settings.MAX_MODALITIES_PER_HEALER:
			modality.healer.add(self.added_by)

		self.send_notification(modality)

		return modality

	def clean_title(self):
		return self.cleaned_data['title'].title()


	def clean_description(self):
		soup = BeautifulSoup(self.cleaned_data['description'])

		if len(soup.get_text()) < 300:
			raise forms.ValidationError(u"Please write at least 300 characters about this Specialty")

		return html_sanitize(self.cleaned_data['description'])


	def send_notification(self, modality):
		subject = "New Specialty: %s" % modality.title
		message_body = u"Description:\n%s\n\nHealer: %s, %s\n\n%s" % \
			               (modality.description.decode('utf-8'),
								unicode(self.added_by.user.client).decode('utf-8'),
								self.added_by,
			               self.added_by.user.email
		               )
		send_queued_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, [o[1] for o in settings.ADMINS])


	class Meta:
		model = Modality
		fields = ('title', 'category', 'description')
