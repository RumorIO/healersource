# coding=utf-8
from django import forms
from dashboard.models import HealerMails


class HealerMailsForm(forms.ModelForm):
	class Meta:
		model = HealerMails
		fields = ['title', 'body', 'body_html', 'email_from', 'delay', 'once', 'process']
