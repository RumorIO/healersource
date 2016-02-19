import re

from django.core.mail import mail_admins

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ErrorReport


class ErrorReportView(APIView):
	def post(self, request, format=None):
		report = re.sub(r'password\d?=[^&]*', '', request.POST['report'])
		if request.user.is_authenticated():
			name, email = request.user.get_full_name(), request.user.email
		else:
			name, email = 'Anonymous', ''

		report = [str(request.user),
					name,
					email,
					request.META.get('HTTP_USER_AGENT', ''),
					request.META.get('HTTP_REFERER', ''),
					report]
		report = "\n".join(report)
		ErrorReport.objects.create(report=report)
		mail_admins('Error', report)
		return Response()
