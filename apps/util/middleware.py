
class BaseTemplateMiddleware(object):
	def process_request(self, request):
		request.BASE_TEMPLATE = "site_base.html" if request.user.is_authenticated() else "base_new_box.html"


class ExceptionUserInfoMiddleware(object):
	"""
	Adds user details to request context on receiving an exception, so that they show up in the error emails.
	Add to settings.MIDDLEWARE_CLASSES and keep it outermost(i.e. on top if possible). This allows
	it to catch exceptions in other middlewares as well.
	"""
	def process_exception(self, request, exception):
		try:
			if request.user.is_authenticated():
				request.META['USER_FULL_NAME'] = str(request.user.client)
				request.META['USER_EMAIL'] = str(request.user.email)
		except:
			pass


class TrackingMiddleware(object):
	def process_request(self, request):
		if request.method == 'GET':
			tracking_code = request.session.get('tracking_code', {})
			fb = request.GET.get('fb_signup_code', False)
			google = request.GET.get('google_signup_code', False)
			if fb:
				tracking_code['fb'] = fb
			if google:
				tracking_code['google'] = google

			if tracking_code:
				request.session['tracking_code'] = tracking_code
