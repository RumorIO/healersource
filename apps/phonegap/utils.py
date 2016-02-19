from django.conf import settings
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.shortcuts import render_to_response


def render_page(request, template, context, extra_context):
	if extra_context:
		context = dict(context, **extra_context)

	if request is None:
		return render_to_string(template, context)
	else:
		return render_to_response(template, context,
			context_instance=RequestContext(request))


def get_phonegap_version(app_version, output_string=False):
	def get_current_version():
		if app_version == 1:
			path = settings.PHONEGAP_VERSION_FILE_PATH
		else:
			path = settings.PHONEGAP_VERSION2_FILE_PATH
		with open(path, 'r') as f:
			return int(f.readline())

	if app_version == 1:
		version = settings.PHONEGAP_VERSION
	else:
		version = settings.PHONEGAP_VERSION2
	version += [get_current_version()]
	if output_string:
		version = '.'.join(map(str, version))
	return version


def template_as_string(template_name, replace_quotes=False):
	template = 'phonegap/' + template_name
	data = render_to_string(template).replace('\n', ' ').replace('\t', ' ')
	if replace_quotes:
		data = data.replace("'", "\\'")
	return data
