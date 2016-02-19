import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import loader
from django.template.context import RequestContext, Context
from django.template.loader import render_to_string

from rest_framework.response import Response
from rest_framework.views import APIView

from account_hs.authentication import user_authenticated
from account_hs.views import (UserAuthenticated, UserLoggedIn,
	EmailPasswordAuthentication)
from dashboard.services.mail_sender import MailSender
from healers.models import Healer, Zipcode, check_wellness_center_provider_perm
from healers.views import get_healers_geosearch
from healers.utils import get_username, get_healer
from healers.forms import HealerSearchForm

from modality.models import ModalityCategory, Modality, save_modality_menu
from modality.forms import ModalityForm


class Update(UserAuthenticated):
	def post(self, request, modality_id, format=None):
		if request.user.is_superuser:
			title = request.POST['title']
			description = request.POST['description']
			visible = json.loads(request.POST['visible'])

			if modality_id:
				modality = Modality.objects.get(pk=modality_id)
			else:
				modality = Modality()

			modality.title = title
			modality.description = description
			modality.visible = visible
			modality.save()

		return Response()


class AddCategory(UserAuthenticated):
	def post(self, request, modality_id, category_id, format=None):
		if request.user.is_superuser:
			modality = Modality.objects.get(pk=modality_id)
			category = ModalityCategory.objects.get(pk=category_id)
			modality.category.add(category)
		return Response()


class RemoveCategory(UserAuthenticated):
	def post(self, request, modality_id, category_id, format=None):
		if request.user.is_superuser:
			modality = Modality.objects.get(pk=modality_id)
			category = ModalityCategory.objects.get(pk=category_id)
			modality.category.remove(category)
		return Response()


class GetModalities(APIView):
	def get(self, request, category_id, format=None):
		if category_id == "all":
			modalities = Modality.objects_approved.filter(visible=True).order_by("title")
		elif category_id == "other":
			categories = ModalityCategory.objects.all()
			modalities = Modality.objects_approved.filter(visible=True).exclude(category__in=categories).order_by("title")
		else:
			modalities = Modality.objects_approved.filter(visible=True).filter(category=category_id).order_by("title")
		html = render_to_string("modality/modality_list.html", {"modalities": modalities})
		return Response(html)


class AddHealer(EmailPasswordAuthentication):
	def post(self, request, modality_id, format=None):
		self.get_initial_data()
		username = request.POST.get('username', None)
		try:
			if self.user.username != username:
				wcenter, healer = check_wellness_center_provider_perm(self.user, username)
				if not healer:
					raise Healer.DoesNotExist
			else:
				healer = Healer.objects.get(user=self.user)
		except Healer.DoesNotExist:
			return Response()

		try:
			modality = Modality.objects_approved.get_with_unapproved(healer).get(pk=modality_id)
		except Modality.DoesNotExist:
			return Response()

		try:
			modality.healer.get(pk=healer.id)
			return Response()
		except Healer.DoesNotExist:
			pass

		if healer.modality_set.count() < settings.MAX_MODALITIES_PER_HEALER:
			modality.healer.add(healer)
		else:
			return Response()

		if healer.default_modality == '':
			healer.default_modality = unicode(modality)
			healer.save()

		try:
			save_modality_menu()
		except Exception:
			pass

		return Response({
			'id': modality_id,
			'title': modality.title
		})


class RemoveHealer(EmailPasswordAuthentication):
	def post(self, request, modality_id, format=None):
		username = request.POST['username']
		self.get_initial_data()

		if self.user.username == username:
			try:
				healer = Healer.objects.get(user__username__iexact=username)
			except Healer.DoesNotExist:
				return Response()

		else:
			wcenter, healer = check_wellness_center_provider_perm(self.user, username)
			if not healer:
				return Response()

		try:
			modality = Modality.objects_approved.get_with_unapproved(healer).get(pk=modality_id)
		except Modality.DoesNotExist:
			return Response()

		modality.healer.remove(healer)

		if healer.modality_set.count() == 0:
			healer.default_modality = settings.DEFAULT_MODALITY_TEXT
			healer.save()

		try:
			save_modality_menu()
		except Exception:
			pass

		return Response({'id': modality_id})


@login_required
def modality_add(request, username=None, template_name="modality/modality_form.html"):
	username = get_username(request, username)
	healer = get_healer(request.user, username)
	if not 'modality_back_url' in request.session:
		request.session['modality_back_url'] = request.META.get('HTTP_REFERER', reverse('healer_edit'))
	specialty_name = None
	form = ModalityForm(request.POST or None, initial={'title': request.GET.get('title', '')}, added_by=healer)
	modality_back_url = None
	if form.is_valid():
		modality = form.save()
		specialty_name = modality.title
		modality_back_url = request.session.pop('modality_back_url')

	return render_to_response(template_name, {
		"form": form,
		"specialty_name": specialty_name,
		"back_url": modality_back_url
	}, context_instance=RequestContext(request))


def modality_list(request, template_name="modality/modalities.html"):
	categories = ModalityCategory.objects.all().order_by("title")

	if request.user.is_superuser:
		modalities = Modality.objects_approved.all().order_by("title").defer("description")
	else:
		modalities = Modality.objects_approved.filter(visible=True).order_by("title").defer("description")

	unapproved_modalities, rejected_modalities = None, None
	if request.user.is_superuser:
		unapproved_modalities = Modality.objects.filter(
			approved=False, rejected=False, visible=True).order_by('-id')
		rejected_modalities = Modality.objects.filter(
			rejected=True, visible=True).order_by('-id')

	return render_to_response(template_name, {
		'base_template': 'base_floatbox.html' if 'fb' in request.GET else 'base_new_box.html',
		'categories': categories,
		'modalities': modalities,
		'unapproved_modalities': unapproved_modalities,
		'rejected_modalities': rejected_modalities,
	}, context_instance=RequestContext(request))


def modality_description(request, modality_id, full_page=False):
	try:
		healer = None
		if modality_id:
			if request.user.is_superuser:
				modality = Modality.objects
				healer = get_object_or_404(Healer, user__username=request.user.username)
			else:
				modality = Modality.objects_approved

			modality = modality.get(pk=modality_id)

		else:
			modality = None

		providers = None
		if modality is not None:
			providers = get_healers_geosearch(request,
				modality_id=modality)[0][:settings.MAX_PROVIDERS_ON_SPECIALITY_PAGE]
		initial_data = {}
		session_data = request.session.get('search_state', None)
		if session_data is not None:
			initial_data.update(session_data)
		no_city = not request.session.get('point', False)
		initial_data['modality_id'] = modality_id
		form = HealerSearchForm(initial=initial_data)

		ctx = {
			"modality": modality,
			"user": request.user,
			"healer": healer,
			'full_page': full_page,
			"base_template": 'base_common.html' if full_page else 'base_blank.html',
			'providers': providers,
			'form': form,
			'no_city': no_city,
		}

		if request.user.is_superuser:
		#			already = ModalityCategory.objects.filter(modality=modality)
		#			c['categories'] = ModalityCategory.objects.exclude(pk__in=already)
			ctx['categories'] = ModalityCategory.objects.filter(modality=modality)
			ctx['category_options'] = ModalityCategory.objects.exclude(modality=modality)

	except Modality.DoesNotExist:
		raise Http404

	return render_to_response("modality/modality.html", ctx, context_instance=RequestContext(request))


def modality_providers(request, modality_id, zipcode=None):

	if zipcode:
		try:
			zipcode_object = Zipcode.objects.get(code=zipcode)
		except Zipcode.DoesNotExist:
			return HttpResponse("Could not find Zipcode " + zipcode)

		request.session['point'] = zipcode_object.point
		zipcode = zipcode_object.code
		request.session['zipcode'] = zipcode
	else:
		zipcode = request.session.get('zipcode', None)

	if not zipcode:
		t = loader.get_template("modality/modality_get_zipcode.html")
		return HttpResponse(t.render(Context({"modality_id": modality_id})))

	NUM_PROVIDERS = 20

	try:
		modality = Modality.objects_approved.get(pk=modality_id)
	except Modality.DoesNotExist:
		return HttpResponse("Could not find Modality " + modality_id)

	providers, more = get_healers_geosearch(request, NUM_PROVIDERS, modality_id=modality_id)
	provider_count = len(providers)

#			if provider_count < NUM_PROVIDERS:
#				providers = set(list(providers) + list(Healer.objects.filter(modality=modality_id)[:NUM_PROVIDERS-provider_count]))

	providers = [p.user for p in providers]
	show_more = provider_count == NUM_PROVIDERS  # just approximate for now

	return render_to_response("modality/modality_providers.html", {
		"modality": modality,
		"user": request.user,
		"providers": providers,
		"show_more_link": show_more,
		"zipcode": zipcode
	})


@user_authenticated
@permission_required('super_duper_user')
def modality_approve(request, modality_id):
	"""
	Approves modality by id, for admins only
	"""
	modality = Modality.objects.get(id=modality_id)
	modality.rejected = False
	modality.approved = True
	modality.save()

	if modality.added_by is not None:
		context = {
			'modality': modality,
		}
		mailsender = MailSender(
			'new_modality_accept', modality.added_by.user, **context)
		mailsender.send_emails()

	return redirect('modailty_list')


@user_authenticated
@permission_required('super_duper_user')
def modality_reject(request, modality_id):
	"""
	Approves modality by id, for admins only
	"""
	modality = Modality.objects.get(id=modality_id)
	modality.rejected = True
	modality.approved = False
	modality.save()

	if modality.added_by is not None:
		context = {
			'modality': modality,
		}
		mailsender = MailSender(
			'new_modality_reject', modality.added_by.user, **context)
		mailsender.send_emails()

	return redirect('modailty_list')


@user_authenticated
def modality_remove(request, modality_id):
	if request.user.is_superuser:
		Modality.objects.get(pk=modality_id).delete()

	return redirect('modailty_list')
