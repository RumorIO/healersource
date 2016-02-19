from django.conf import settings

class DowntimeMiddleware(object):
	def process_request(self, request):
		request.DOWNTIME_MESSAGE = settings.DOWNTIME_MESSAGE
