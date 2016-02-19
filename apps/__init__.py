from django.conf import settings
from django.http import HttpResponseServerError
from django.template import loader
from django.template.context import RequestContext
from django.template.defaulttags import URLNode
from django.contrib.sites.models import Site


def server_error(request, template_name="500.html"):
	t = loader.get_template(template_name)
	ctx = RequestContext(request)
	return HttpResponseServerError(t.render(ctx))

_URL_RENDER_UPDATED = False
if not _URL_RENDER_UPDATED:
	old_render = URLNode.render

	def new_render(cls, context):
		"""Override existing url to always include hostname."""
		scheme = getattr(settings, 'DEFAULT_HTTP_PROTOCOL', 'http')
		url = old_render(cls, context)
		if cls.asvar:
			url = context[cls.asvar]

		if not url.startswith('http'):
			url = '{}://{}{}'.format(
				scheme,
				Site.objects.get_current(),
				url)

		if cls.asvar:
			context[cls.asvar] = url
			return ''

		return url

	URLNode.render = new_render
	_URL_RENDER_UPDATED = True
