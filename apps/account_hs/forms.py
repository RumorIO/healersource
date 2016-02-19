import re
import traceback
from collections import OrderedDict

from django.db.utils import IntegrityError
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.mail import mail_admins
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.http import int_to_base36
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django import forms

from pinax.apps.account.models import PasswordReset, EmailAddress, EmailConfirmation
from pinax.apps.account.forms import (LoginForm, GroupForm,
	ResetPasswordKeyForm, ResetPasswordForm)
from friends.models import JoinInvitation

from util import get_name

from ambassador.handlers import set_ambassador
from clients.models import SiteJoinInvitation, create_dummy_user
from account_hs.exceptions import ResetPasswordSeveralEmailsNotVerified
from account_hs.utils import (login_user, get_or_create_email_address,
							after_signup)


def validate_only_numbers_and_spaces(text):
	match = re.match(r'^[0-9\w ]+$', text, re.UNICODE)
	if match is None:
		raise ValidationError('Only letters, numbers, spaces are allowed.')


def exclude_users_with_unusable_passwords(users):
	return [u for u in users if u.has_usable_password()]


def clean_password(password):
	if len(password) < 8:
		raise forms.ValidationError(_("Password should be at least 8 characters long."))
	return password


def find_user(email):
	users = User.objects.filter(email__iexact=email).exclude(is_active=False)
	return users
	# return exclude_users_with_unusable_passwords(users)


def validate_email(email):
	"""
	Check not dummy users with same email
	Dummy user: is_active = False, unusable password
	"""
	count_users = len(find_user(email))
	if count_users:
		raise forms.ValidationError(
			mark_safe(_("Another user is already registered with this email address. "
						"You can <a href='%s'>Log In</a> or <a href='%s'>Reset Your Password</a>.")
				% (reverse('login_page'), reverse('acct_passwd_reset'))))
	return email


class LoginFormHS(LoginForm):

	def __init__(self, *args, **kwargs):
		super(LoginFormHS, self).__init__(*args, **kwargs)
		self.fields = OrderedDict((k, self.fields[k]) for k in self.fields.keyOrder)
		self.fields['remember'].initial = True
		self.fields['email'].widget.attrs['placeholder'] = 'Your Email Address'
		self.fields['email'].widget.attrs['autofocus'] = 'autofocus'
		self.fields['password'].widget.attrs['placeholder'] = 'Password'

	def clean(self):
		try:
			cleaned_data = super(LoginFormHS, self).clean()
			return cleaned_data
		except forms.ValidationError as ve:
			if 'inactive' in str(ve):
				users = User.objects.filter(email=self.cleaned_data["email"])
				users = exclude_users_with_unusable_passwords(users)
				if users:
					email_address = get_or_create_email_address(users[0], primary=True)
					EmailConfirmation.objects.send_confirmation(email_address)

				raise forms.ValidationError(_("Your email address is not confirmed. Please check your email and click on the link."))
			raise ve


class ClientSignupForm(GroupForm):
	first_name = forms.CharField(
		label=_('Full Name'),
		max_length=30,
		widget=forms.TextInput(attrs={'placeholder': 'Full Name'}),
		validators=[validate_only_numbers_and_spaces]
	)

	email = forms.EmailField(
		label=_("E-mail"),
		widget=forms.TextInput(attrs={'placeholder': 'E-mail', 'type': 'email'})
	)
	password1 = forms.CharField(
		label=_("Password"),
		widget=forms.PasswordInput(
			render_value=False,
			attrs={'placeholder': 'Password: 8 Characters Minimum'})
	)
	password2 = forms.CharField(
		label=_("Password (again)"),
		widget=forms.PasswordInput(
			render_value=False,
			attrs={'placeholder': 'Password again: To Prevent Typos'})
	)
	confirmation_key = forms.CharField(
		max_length=40,
		widget=forms.HiddenInput(),
		required=False
	)

	#	healer_or_client = forms.ChoiceField(
	#			label="Account Type",
	#			widget=forms.RadioSelect(),
	#			choices=( ("client", "Client"), ("healer", "Provider") )
	#		)

	def __init__(self, *args, **kwargs):
		super(ClientSignupForm, self).__init__(*args, **kwargs)
		if self.initial.get('confirmation_key', False) or self.data.get('confirmation_key', False):
			del self.fields['email']

	def clean_email(self):
		return validate_email(self.cleaned_data['email'])

	def clean_password1(self):
		return clean_password(self.cleaned_data["password1"])

	def clean_confirmation_key(self):
		if self.cleaned_data['confirmation_key']:
			try:
				JoinInvitation.objects.get(confirmation_key=self.cleaned_data["confirmation_key"])
			except JoinInvitation.DoesNotExist:
				raise forms.ValidationError(_("Invalid confirmation key."))
		return self.cleaned_data["confirmation_key"]

	def clean(self):
		if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
			if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
				raise forms.ValidationError(_("You must type the same password each time."))
		return self.cleaned_data

	def create_user(self, email, commit=True, create_real_username=False):
		first_name, last_name = get_name(self.cleaned_data.get('first_name', ''))
		password = self.cleaned_data["password1"]

		if not email.strip():
			return None

		# find inactive user with the same password
		# to repeat signup steps in phonegap app without user duplication
		if password:
			users = User.objects.filter(email=email, is_active=False)
			for user in users:
				if user.check_password(password):
					return user

		user = create_dummy_user(
			first_name,
			last_name,
			email,
			False,
			create_real_username,
		)

		#set username for Healers only - Clients get a dummy username so all the urls dont get used up
#		user.username = self.cleaned_data['username'].lower()
		if password:
			user.set_password(password)

		if commit:
			user.save()

		return user

	def login(self, request, user):
		login_user(request, user)

	def save(self, account_type="client", **kwargs):
		is_superuser = kwargs.pop('is_superuser', False)
		cookies = kwargs.pop('cookies', None)
		join_invitation_from_user = None

		if self.cleaned_data['confirmation_key']:
			join_invitation = SiteJoinInvitation.objects.get(confirmation_key=self.cleaned_data["confirmation_key"])
			join_invitation_from_user = join_invitation.from_user
			email = join_invitation.contact.email

			new_user = self.create_user(email)
			if not new_user:
				return None

			new_user.is_active = True
			new_user.save()

			email_address, created = EmailAddress.objects.get_or_create(
				user=new_user, email=email)
			email_address.verified = True
			email_address.primary = True
			email_address.save()
			after_signup(new_user, account_type=account_type)

		else:
			email = self.cleaned_data['email']
			new_user = self.create_user(email)
			if not new_user:
				return None

			email_address, created = EmailAddress.objects.get_or_create(
				user=new_user, email=email)

			if is_superuser:
				new_user.is_active = True
				new_user.save()

				email_address.verified = True
				email_address.primary = True
				email_address.save()
				email_confirmed = True
			else:
				#request email confirmation
				EmailConfirmation.objects.send_confirmation(email_address, **kwargs)
				email_confirmed = False

			after_signup(new_user, account_type=account_type, email_confirmed=email_confirmed)

		set_ambassador(
			client_user=new_user,
			ambassador_user=join_invitation_from_user,
			cookies=cookies)

		return new_user


class ClientSignupNoNameForm(ClientSignupForm):
	def __init__(self, *args, **kwargs):
		super(ClientSignupNoNameForm, self).__init__(*args, **kwargs)
		self.fields['first_name'].required = False


class ClientSignupWithLastNameForm(ClientSignupForm):
	def __init__(self, *args, **kwargs):
		super(ClientSignupWithLastNameForm, self).__init__(*args, **kwargs)
		self.fields['first_name'].widget = forms.TextInput(attrs={'placeholder': 'First Name'})

	last_name = forms.CharField(
		label=_('Last Name'),
		max_length=30,
		widget=forms.TextInput(attrs={'placeholder': 'Last Name'}),
		validators=[validate_only_numbers_and_spaces]
	)


class HealerSignupForm(ClientSignupForm):
	def create_user(self, email, commit=True):
		user = super(HealerSignupForm, self).create_user(email, False, True)

		if not user:
			return None

		if commit:
			try:  # meant to fix #1024
				user.save()
			except IntegrityError:
				mail_admins('HealerSignupForm Error', traceback.format_exc())

		return user

	def save(self, request=None, **kwargs):
		return super(HealerSignupForm, self).save(account_type='healer', **kwargs)


class WellnessCenterSignupForm(HealerSignupForm):
	# def __init__(self, *args, **kwargs):
	# 	super(WellnessCenterSignupForm, self).__init__(*args, **kwargs)
	# 	self.fields['first_name'].widget = forms.TextInput(attrs={'placeholder': 'Spa or Center Name'})

	def save(self, request=None, **kwargs):
		return super(HealerSignupForm, self).save(account_type='wellness_center', **kwargs)


class PasswordLengthResetPasswordKeyForm(ResetPasswordKeyForm):
	"""
	Extended reset password form
	- check password length
	- confirm email on save
	"""
	def clean_password1(self):
		return clean_password(self.cleaned_data["password1"])

	def save(self):
		super(PasswordLengthResetPasswordKeyForm, self).save()
		EmailAddress.objects.filter(
			user=self.user,
			emailconfirmation__confirmation_key=self.temp_key,
			verified=False
		).update(verified=True)
		self.user.is_active = True
		self.user.save()


class ResetPasswordFormHS(ResetPasswordForm):

	def clean_email(self):
		email = self.cleaned_data["email"]
		emails = EmailAddress.objects.filter(email__iexact=email)
		verified = [ea for ea in emails if ea.verified]
		not_verified = [ea for ea in emails if not ea.verified]
		if len(verified):
			return email
		if len(not_verified) > 1:
			raise ResetPasswordSeveralEmailsNotVerified()
		elif len(not_verified) == 1:
			return email
		else:
			raise forms.ValidationError(
				_("Email address not verified for any user account")
			)
		return email

	def save(self, **kwargs):

		email = self.cleaned_data["email"]
		token_generator = kwargs.get("token_generator", default_token_generator)

		email_addresses = EmailAddress.objects.filter(
			email__iexact=email)
		for email_address in email_addresses:
			user = email_address.user

			temp_key = token_generator.make_token(user)

			# save it to the password reset model
			password_reset = PasswordReset(user=user, temp_key=temp_key)
			password_reset.save()

			# save it to the email confirmation model
			if not email_address.verified:
				EmailConfirmation.objects.create(
					email_address=email_address,
					confirmation_key=temp_key,
					sent=settings.GET_NOW()
				)

			current_site = Site.objects.get_current()
			domain = unicode(current_site.domain)

			# send the password reset email
			subject = _("HealerSource Password Reset")
			message = render_to_string(
				"account/password_reset_key_message.txt",
				{
					"user": user,
					"uid": int_to_base36(user.id),
					"temp_key": temp_key,
					"domain": domain,
					"email": email
				})
			from healers.utils import send_regular_mail
			send_regular_mail(
				subject,
				message,
				settings.DEFAULT_FROM_EMAIL,
				[user.email])
		return self.cleaned_data["email"]
