from oauth2client import xsrfutil
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.django_orm import Storage
from provider.oauth2.views import AccessTokenView as AccessTokenViewOriginal
from provider.views import OAuthError

from django.conf import settings
from django.template.context import RequestContext
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response

from account_hs.authentication import user_authenticated

from .forms import PasswordGrantForm
from .models import Credentials

FLOW = OAuth2WebServerFlow(**settings.OAUTH_ACCESS_SETTINGS['google'])


@user_authenticated
def google(request):
	storage = Storage(Credentials, 'id', request.user, 'google_credential')
	credential = storage.get()
	if credential is None or credential.invalid:
		FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
			request.user)
		authorize_url = FLOW.step1_get_authorize_url()
		return HttpResponseRedirect(authorize_url)
	else:
		redirect_url = request.session.pop('oauth_callback_redirect', 'google_calendar_sync_run')
		return redirect(redirect_url)


@user_authenticated
def auth_return(request):
	error = request.GET.get('error', False)
	if error == 'access_denied':
		return render_to_response('oauth_access/oauth_error.html', {
			'error': 'Access Denied',
		}, context_instance=RequestContext(request))

	if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.REQUEST['state']),
			request.user):
		return HttpResponseBadRequest()
	credential = FLOW.step2_exchange(request.REQUEST)
	storage = Storage(Credentials, 'id', request.user, 'google_credential')
	storage.put(credential)
	redirect_url = request.session.pop('oauth_callback_redirect', 'google_calendar_sync_run')
	return redirect(redirect_url)


class AccessTokenView(AccessTokenViewOriginal):
	def get_password_grant(self, request, data, client):
		form = PasswordGrantForm(data, client=client)
		if not form.is_valid():
			raise OAuthError(form.errors)
		return form.cleaned_data
