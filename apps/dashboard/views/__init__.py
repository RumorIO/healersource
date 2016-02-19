from django.conf import settings
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

from account_hs.authentication import user_is_superuser
from healers.models import WellnessCenter
from emailconfirmation.models import EmailAddress


@user_is_superuser
@require_http_methods(['GET'])
def index(request):
	return TemplateResponse(request, 'dashboard/index.html', {})


@user_is_superuser
def unconfirmed_list(request):
	emails = EmailAddress.objects.filter(
		verified=False, user__is_active=False).order_by(
			'-user__date_joined').select_related('user')

	return render_to_response('dashboard/unconfirmed_list.html', {
		'emails': emails,
		}, context_instance=RequestContext(request))


@user_is_superuser
def confirm_email(request, id):
	if not request.user.is_superuser:
		raise Http404

	email = get_object_or_404(EmailAddress, pk=id)
	email.verified = True
	email.primary = True
	email.save()
	user = email.user
	user.is_active = True
	user.save()
	return redirect('dashboard:unconfirmed_list')


@user_is_superuser
def custom_schedule_payments_center_list(request):
	"""List centers which have added cards."""
	user_ids = WellnessCenter.objects.filter(user__customer__isnull=False).values_list('user', flat=True)
	users = User.objects.filter(pk__in=user_ids)
	users = [u for u in users if u.customer.can_charge()]
	return render_to_response('dashboard/custom_schedule_payments_center_list.html', {
		'users': users,
		}, context_instance=RequestContext(request))


@user_is_superuser
def custom_schedule_payment_center(request, username):
	user = User.objects.get(username=username)

	return render_to_response('dashboard/custom_schedule_payment_center.html', {
		'user': user,
		'amounts': settings.CUSTOM_SCHEDULE_PAYMENT_AMOUNTS,
		}, context_instance=RequestContext(request))


@user_is_superuser
def delete_account(request):
	return render_to_response('dashboard/delete_account.html', {
		}, context_instance=RequestContext(request))
