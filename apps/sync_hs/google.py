import gdata
from oauth2_hs.models import Credentials
import httplib2
import apiclient
import oauth2client


class GoogleClient(object):
	"""Base class for google services."""

	def __init__(self, user):
		self.batch = None
		self.http = self.get_credentials(user).authorize(httplib2.Http())

	def get_credentials(self, user):
		credentials = oauth2client.django_orm.Storage(
			Credentials, 'id', user, 'google_credential').get()
		if credentials is None or credentials.invalid:
			raise oauth2client.client.Error()
		return credentials

	def build_service(self, service, version):
		return apiclient.discovery.build(service, version, http=self.http)


class GoogleDataClientError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class GoogleDataClient(GoogleClient):
	""" Base class for google data services. """

	def __init__(self, user):
		auth2token = gdata.gauth.OAuth2TokenFromCredentials(self.get_credentials(user))
		self.client = auth2token.authorize(self.client)
