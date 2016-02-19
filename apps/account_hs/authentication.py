from django.conf import settings
from django.core import serializers
from django.core.mail import mail_admins
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User

from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication


class CaseInsensitiveAuthenticationBackend(ModelBackend):

	def authenticate(self, **credentials):
		lookup_params = {}
		if settings.ACCOUNT_EMAIL_AUTHENTICATION:
			if 'email' in credentials:
				lookup_params["email__iexact"] = credentials["email"]
			else:
				lookup_params["email__iexact"] = credentials["username"]
		else:
			lookup_params["username"] = credentials["username"]
		try:
			user = User.objects.get(**lookup_params)
		except User.DoesNotExist:
			return None
		except User.MultipleObjectsReturned:
			users = User.objects.filter(**lookup_params)
			message = serializers.serialize('json', users)
			mail_admins('Multiple user login error', message)
			users_inactive = users.filter(is_active=False)
			number_of_users = len(users)
			number_of_inactive_users = len(users_inactive)
			users_to_delete = []
			if number_of_inactive_users in [number_of_users, 0]:
				users_to_delete = users[:number_of_users - 1]
			else:
				users_inactive.delete()
				users = User.objects.filter(**lookup_params)
				number_of_users = len(users)
				if number_of_users > 1:
					users_to_delete = users[:number_of_users - 1]

			for u in users_to_delete:
				u.delete()
			user = users[0]
		if user.check_password(credentials["password"]):
			return user

	def has_perm(self, user, perm, obj=None):
		# @@@ allow all users to add wiki pages
		wakawaka_perms = [
			"wakawaka.add_wikipage",
			"wakawaka.add_revision",
			"wakawaka.change_wikipage",
			"wakawaka.change_revision"
		]
		if perm in wakawaka_perms:
			return True
		return super(CaseInsensitiveAuthenticationBackend, self).has_perm(user, perm, obj)


def user_authenticated(view_func):
	active_required = user_passes_test(lambda u: u.is_active)
	decorated_view_func = login_required(active_required(view_func))
	return decorated_view_func


def user_is_superuser(view_func):
	active_required = user_passes_test(lambda u: u.is_superuser)
	decorated_view_func = login_required(active_required(view_func))
	return decorated_view_func


class RestSessionAuthentication(SessionAuthentication):
	def authenticate(self, request):
		"""
		Returns a `User` if the request session currently has a logged in user.
		Otherwise returns `None`.
		"""

		# Get the underlying HttpRequest object
		request = request._request
		user = getattr(request, 'user', None)
		# Unauthenticated, CSRF validation not required
		if not user or user.is_anonymous():
			return None

		self.enforce_csrf(request)

		# CSRF passed with authenticated user
		return (user, None)


class IsActiveUser(permissions.BasePermission):
	"""Only Active Users have permission."""

	def has_permission(self, request, view):
		return request.user.is_active


EmailModelBackend = CaseInsensitiveAuthenticationBackend
