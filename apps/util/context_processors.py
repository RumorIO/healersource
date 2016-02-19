def impersonate(request):
	if request.user.is_authenticated():
		#for k,v in request.session.items():
		#    print '%s: %s' % (k, v)
		original_user = request.session.get('original_user', False)
		if original_user:
			return {'impersonate': original_user}
		try:
			profile = request.user.username
		except AttributeError:
			return {'impersonate': None}
		if request.user.is_superuser:
			return {'impersonate': profile}

	return {}
