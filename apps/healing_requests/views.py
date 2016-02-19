from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth import authenticate
from django.contrib import messages
from django.core.urlresolvers import reverse
from healers.utils import is_healer
from messages_hs.forms import ComposeFormUnregistered
from messages_hs.models import MessageExtra

from endless_pagination.decorators import page_template
from django.utils.decorators import method_decorator
from modality.models import Modality, ModalityCategory

from healing_requests.forms import (HealingRequestForm,
	HealingRequestSearchForm, HealingRequestUserFormUnregistered)
from healing_requests.models import (HealingRequest, HealingRequestSearch,
	process_specialities)


def save_specialities(instance, specialities):
	for speciality in specialities:
		speciality_obj = Modality.objects.get(id=speciality)
		instance.specialities.add(speciality_obj)


def save_speciality_categories(instance, speciality_categories):
	for s_category in speciality_categories:
		cat = ModalityCategory.objects.get(id=s_category)
		instance.speciality_categories.add(cat)


def save_specialties_and_specialty_categories(inst, form_data):
	def process_form_data(form_specialities, get_categories=False):
		def get_ids_from_specialities(specialities):
			match_type = 'p' if get_categories else 'c'

			output = set()
			for s in specialities:
				_type, _id = s.split(":")
				if _type == match_type:
					output.add(_id)
			return list(output)

		if form_specialities and form_specialities[0]:
			specialities = process_specialities(form_specialities)
		else:
			return []
		return get_ids_from_specialities(specialities)

	specialities = process_form_data(form_data)
	speciality_categories = process_form_data(form_data, True)
	save_specialities(inst, specialities)
	save_speciality_categories(inst, speciality_categories)


class Home(View):
	template_name = "healing_requests/home.html"

	@method_decorator(page_template('healing_requests/recent_requests_page.html', key='recent_requests_page'))
	@method_decorator(page_template('healing_requests/saved_searches_page.html', key='saved_searches_page'))
	@method_decorator(page_template('healing_requests/search_results_page.html', key='search_results_page'))
	def dispatch(self, *args, **kwargs):
		return super(Home, self).dispatch(*args, **kwargs)

	def get(self, request, *args, **kwargs):
		context = self.get_context_data(*args, **kwargs)
		user = request.user

		if self.request.GET.get('search', None):
			if not user.is_authenticated():
				user = None

			form = HealingRequestSearchForm(request.GET)
			if form.is_valid():
				form_data = form.cleaned_data

				instance = form.save()
				instance.user = user
				instance.save()
				if (form_data.get("search_specialities", None) and
						form_data.get('only_my_specialities', None) is False):
					save_specialties_and_specialty_categories(instance, form_data.get('search_specialities'))

				return redirect(reverse("show_healing_request_search", args=[instance.id]))

			# HealingRequestSearch.save_search(request.GET, user)
		elif is_healer(user) and not 'show_search' in request.GET:
			saved_searches = HealingRequestSearch.objects.filter(
				user=user, saved=True)
			if saved_searches.count() > 0:
				return redirect(reverse("show_healing_request_search", args=[saved_searches[0].id]))

		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		def process_new_hr():
			healing_request = request_form.save(commit=False)
			healing_request.user = user
			healing_request.save()
			save_specialties_and_specialty_categories(healing_request, request_form.cleaned_data['specialities'])
			healing_request.mail_matched_searches()
			# messages.success(request, 'Your request submitted successfully')
			if 'new_user_hr' in request.session:
				email = request.session['new_user_hr'].email
				return render(request, 'account/signup_thanks.html', {
					'thanks_message': render_to_string('account/verification_sent_message.html',
						{'email': email,
							'new_hr_user': True}),
					'email': email})
			return redirect(reverse('healing_request_home'))

		user_logged_in = request.user.is_authenticated()
		context = self.get_context_data(*args, **kwargs)
		request_form = HealingRequestForm(request.POST)
		user = None
		# client = None
		client_signup_form = None
		if not user_logged_in:
			client_signup_form = HealingRequestUserFormUnregistered(request.POST)

			if client_signup_form.is_valid():

				user = client_signup_form.save()
				# client = Client.objects.get(user=user)
				user = authenticate(
					username=user.username,
					password=client_signup_form.cleaned_data['password1'],
					email=user.email)
				# login(request, user)
				request.session['new_user_hr'] = user
		else:
			user = request.user
			# client = Client.objects.get(user=user)

		if not user_logged_in:
			# if client_signup_form.is_valid() and request_form.is_valid():
			if 'new_user_hr' in request.session and request_form.is_valid():
				user = request.session['new_user_hr']
				return process_new_hr()
			else:
				context['client_signup_form'] = client_signup_form
				context['request_form'] = request_form
		else:
			if request_form.is_valid():
				return process_new_hr()
			else:
				context['request_form'] = request_form

		return render(request, self.template_name, context)

	def get_context_data(self, *args, **kwargs):
		if kwargs.get('template', None):
			self.template_name = kwargs['template']
		context = {}
		context['is_healer'] = is_healer(self.request.user)
		context['request_form'] = HealingRequestForm()
		context['client_signup_form'] = HealingRequestUserFormUnregistered()
		if 'search' not in self.request.GET and 'show_search' not in self.request.GET:
			context['recent_requests'] = \
				HealingRequest.objects.filter(user__is_active=True).order_by("-created_at")
		else:
			context['recent_requests'] = []
		user = self.request.user if self.request.user.is_authenticated() else None
		saved_searches = HealingRequestSearch.objects.filter(
			user=user, saved=True).order_by("-created_at")
		context['saved_searches'] = saved_searches

		my_requests = None

		if self.request.user.is_authenticated():
			my_requests = HealingRequest.objects.filter(
				user=self.request.user).order_by('-created_at')

		context['my_requests'] = my_requests

		#search
		context['hr_search_form'] = HealingRequestSearchForm(self.request.GET)
		if self.request.GET.get('search', None) or self.request.GET.get('show_search', None):
			search_params = self.request.GET.copy()
			search_params.update({'is_healer': context['is_healer']})
			context['search_params'] = search_params
			form = HealingRequestSearchForm(search_params)
			cleaned_data = {}
			if form.is_valid():
				cleaned_data = form.cleaned_data
				cleaned_data.update({'is_healer': context['is_healer']})
			context['search_results'] = HealingRequest.search(cleaned_data)
		#end search

		context['list_page'] = True
		context['SOURCE_CHOICE_HR'] = MessageExtra.SOURCE_CHOICE_HR

		context['hide_about'] = 'search' in self.request.GET or 'show_search' in self.request.GET or saved_searches or (my_requests and my_requests.exists())
		return context


def delete_search(request, id):
	instance = HealingRequestSearch.objects.get(id=id)
	instance.saved = False
	instance.save()
	messages.success(request, 'Your have deleted your saved search successfully')

	return redirect(reverse("healing_request_home"))


def show_search(request, id):
	instance = HealingRequestSearch.objects.get(id=id)
	param_string = instance.get_search_param_string()
	url = "%s?%s" % (reverse("healing_request_home"), param_string)
	return redirect(url)


class ShowHealingRequest(TemplateView):
	template_name = 'healing_requests/show_healing_request.html'

	def get_context_data(self, *args, **kwargs):
		context = super(ShowHealingRequest, self).get_context_data(*args, **kwargs)
		context['healing_request'] = get_object_or_404(HealingRequest, id=kwargs['id'])
		context['compose_form'] = ComposeFormUnregistered()
		if 'popup' in self.request.GET:
			self.request.BASE_TEMPLATE = 'base_empty.html'
		return context

# class MyRequestList(TemplateView):
# 	template_name = 'healing_requests/my_requests.html'
#
# 	@method_decorator(page_template('healing_requests/recent_requests_page.html', key='recent_requests_page'))
# 	def dispatch(self, *args, **kwargs):
# 		return super(MyRequestList, self).dispatch(*args, **kwargs)
#
# 	def get_context_data(self, *args, **kwargs):
# 		if kwargs.get('template', None):
# 			self.template_name = kwargs['template']
# 		context = super(MyRequestList, self).get_context_data(*args, **kwargs)
# 		context['recent_requests'] = HealingRequest.objects.filter(
# 			user=self.request.user).order_by('-created_at')
#
# 		return context


def get_healing_request(user, _id):
	return get_object_or_404(HealingRequest, user=user, pk=_id)


class EditHealingRequest(View):
	template_name = 'healing_requests/edit_healing_request.html'

	def get(self, request, *args, **kwargs):
		healing_request = get_healing_request(request.user, kwargs['id'])
		request_form = HealingRequestForm(instance=healing_request)

		context = {
			'request_form': request_form,
			'healing_request': healing_request
		}
		return render(request, self.template_name, context)

	def post(self, request, *args, **kwargs):
		healing_request = get_healing_request(request.user, kwargs['id'])
		request_form = HealingRequestForm(request.POST, instance=healing_request)
		if request_form.is_valid():
			healing_request = request_form.save(commit=False)
			healing_request.user = request.user
			healing_request.save()
			save_specialties_and_specialty_categories(healing_request, request_form.cleaned_data['specialities'])
			return redirect(reverse('healing_request_home'))
		context = {
			'request_form': request_form,
			'healing_request': healing_request
		}

		return render(request, self.template_name, context)


class DeleteHealingRequest(View):
	def post(self, request, *args, **kwargs):
		healing_request = get_healing_request(request.user, kwargs['id'])
		healing_request.delete()
		return redirect(reverse("healing_request_home"))
