from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods
from dashboard.forms.mails import HealerMailsForm
from dashboard.models import HealerMails


@require_http_methods(['GET'])
@permission_required('super_duper_user')
def list(request):
	return TemplateResponse(request, 'dashboard/mails/list.html', {
		'mails': HealerMails.objects.all()
	})


@permission_required('super_duper_user')
def edit(request, slug):
	mails = get_object_or_404(HealerMails, slug=slug)
	form = HealerMailsForm(request.POST or None, instance=mails)
	if form.is_valid():
		form.save()
		return HttpResponseRedirect(reverse('dashboard:mails_list'))
	return TemplateResponse(request, 'dashboard/mails/edit.html', {
		'form': form
	})
