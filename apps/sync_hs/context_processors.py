from oauth_access.access import OAuthAccess


def get_facebook_context():
	try:
		access = OAuthAccess("facebook")
		facebook_callback_url = access.callback_url.replace('http://', 'https://')
		return {'facebook_app_key': access.key,
				'facebook_scopes': access.provider_scope,
				'facebook_callback_url': facebook_callback_url}
	except Exception:
		return {}


def facebook_processor(request):
	return get_facebook_context()
