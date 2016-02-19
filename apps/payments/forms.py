from django import forms

from healers.models import Healer

from .settings import PLAN_CHOICES


class PlanForm(forms.Form):
	# pylint: disable=R0924
	plan = forms.ChoiceField(choices=PLAN_CHOICES + [("", "-------")])


class BookingPaymentsSettingsForm(forms.Form):
	booking_payment_requirement = forms.ChoiceField(choices=Healer.BOOKING_PAYMENT_REQUIREMENT_CHOICES)
	booking_healersource_fee = forms.ChoiceField(
		choices=Healer.BOOKING_HEALERSOURCE_FEE_CHOICES,
		widget=forms.RadioSelect(),
	   label='HealerSource Fee'
	)
