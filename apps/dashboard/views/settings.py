from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods
from dashboard.forms import settings
from dashboard.models import HealerSettings


@require_http_methods(['GET'])
@permission_required('super_duper_user')
def list(request):
	return TemplateResponse(request, 'dashboard/settings/list.html', {
		'settings': HealerSettings.objects.all()
	})


@permission_required('super_duper_user')
def edit(request, key):
	setting = get_object_or_404(HealerSettings, key=key)
	form = settings.HealerSettingsForm(request.POST or None, instance=setting)
	if form.is_valid():
		form.save()
		return HttpResponseRedirect(reverse('dashboard:settings_list'))
	return TemplateResponse(request, 'dashboard/settings/edit.html', {
		'form': form
	})
