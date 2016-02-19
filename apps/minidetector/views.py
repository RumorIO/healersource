from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


def login_redirect(request):
	query_string = request.META.get('QUERY_STRING', False)
	if query_string: query_string = '?' + query_string

	return HttpResponseRedirect(reverse("login_page") + query_string)
