import urllib

from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.urlresolvers import reverse

from provider.forms import OAuthValidationError
from provider.oauth2.forms import PasswordGrantForm as PasswordGrantFormOriginal

from oauth_access.views import oauth_callback


class PasswordGrantForm(PasswordGrantFormOriginal):
	def clean(self):
		def get_user_from_facebook_token(signed_request, access_token):
			def build_url(*args, **kwargs):
				get = kwargs.pop('get', {})
				url = reverse(*args, **kwargs)
				if get:
					url += '?' + urllib.urlencode(get)
				return url

			request = HttpRequest()
			request.user = AnonymousUser()
			request.session = SessionStore()
			request.GET['access_token'] = access_token
			request.GET['signed_request'] = signed_request
			request.REQUEST = {'next': '/'}
			oauth_callback(request, 'facebook')
			return request.user

		data = self.cleaned_data
		user = get_user_from_facebook_token(data['username'], data['password'])
		if user is None or user == AnonymousUser():
			raise OAuthValidationError({'error': 'invalid_grant'})

		data['user'] = user
		return data
