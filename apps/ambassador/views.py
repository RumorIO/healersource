from datetime import datetime, timedelta
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import RedirectView, TemplateView, FormView, View

from oauth_access.models import UserAssociation

from about.views import search
from ambassador.forms import SettingsForm, EmbedSettingsForm
from ambassador.settings import COOKIE_NAME, COOKIE_MAX_AGE
from clients.models import Client
from util.views import LoginRequiredMixin, MultipleFormsView


def set_ambassador_cookie(response, username):
	"""
	Save ambassador username to response cookie
	"""
	expires = datetime.strftime(
		datetime.utcnow() + timedelta(seconds=COOKIE_MAX_AGE),
		"%a, %d-%b-%Y %H:%M:%S GMT")
	response.set_cookie(
		COOKIE_NAME,
		username,
		max_age=COOKIE_MAX_AGE,
		expires=expires)


def check_ambassador_program(username):
	"""
	Check if user has an ambassador program
	"""
	if not username:
		raise Http404

	try:
		client = Client.objects.get(user__username__exact=username)
	except Client.DoesNotExist:
		raise Http404

	if not client.ambassador_program:
		raise Http404

	return client


class AmbassadorRedirectView(RedirectView):
	"""
	Set ambassador cookie and redirects
	"""
	permanent = False

	def get_redirect_url(self, *args, **kwargs):
		# remove ambassador/username from url
		url = '/'.join(self.request.path_info.split('/')[3:])
		return '/' + url

	def get(self, request, *args, **kwargs):
		response = super(AmbassadorRedirectView, self).get(
			request, *args, **kwargs)

		set_ambassador_cookie(response, self.kwargs['username'])
		return response


class StripeRequiredMixin(object):
	"""
	Mixin for class based view to check if stripe connected
	"""
	def dispatch(self, request, *args, **kwargs):
		stripe = UserAssociation.objects.filter(
			user=request.user,
			service='stripe').exists()
		if not stripe:
			return redirect('ambassador:promo')

		return super(StripeRequiredMixin, self).dispatch(
			request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, StripeRequiredMixin, TemplateView):
	"""
	Show ambassador peoples and collected fees
	"""
	template_name = 'ambassador/dashboard.html'

	def get_context_data(self, **kwargs):
		context = super(DashboardView, self).get_context_data(**kwargs)

		link = self.request.build_absolute_uri(
			reverse('ambassador:signup', args=[self.request.user.username]))
		first_level_persons = Client.objects.filter(
			ambassador__user=self.request.user)
		month_fees = 0
		total_fees = 0

		context.update({
			'link': link,
			'first_level_persons': first_level_persons,
			'month_fees': month_fees,
			'total_fees': total_fees
		})
		return context

	def get(self, request, *args, **kwargs):
		"""
		Redirect to settings if ambassador plan is not selected
		"""
		client = request.user.client
		if not client.ambassador_plan:
			return redirect('ambassador:settings')

		return super(DashboardView, self).get(
			request, *args, **kwargs)


class PromoView(LoginRequiredMixin, TemplateView):
	"""
	Show ambassador promo page
	"""
	template_name = 'ambassador/promo.html'

	def get_context_data(self, **kwargs):
		self.request.session['stripe_success_redirect'] = reverse('ambassador:settings')

		context = super(PromoView, self).get_context_data(**kwargs)
		context.update({
			'STRIPE_CONNECT_LINK': settings.STRIPE_CONNECT_LINK
		})
		return context


class SettingsView(LoginRequiredMixin, StripeRequiredMixin, MultipleFormsView):
	"""
	Ambassador settings form and list of links to share
	"""
	template_name = 'ambassador/settings.html'
	form_classes = {
		'ambassador': SettingsForm,
		'embed': EmbedSettingsForm
	}
	success_url = reverse_lazy('ambassador:dashboard')

	def get_context_data(self, **kwargs):
		context = super(SettingsView, self).get_context_data(**kwargs)

		urls = ['front_page', 'tour', 'signup', 'landing_page_notes']
		context['links'] = [
			self.request.build_absolute_uri(
				reverse('ambassador:'+url, args=[self.request.user.username]))
			for url in urls]

		context['embed_plugin_link'] = self.request.build_absolute_uri(
			reverse('ambassador:plugin', args=[self.request.user.username]))

		return context

	def get_form_kwargs(self, active=False):
		kwargs = super(SettingsView, self).get_form_kwargs(active)
		kwargs['client'] = self.request.user.client
		return kwargs

	def form_valid(self, form):
		form.save()
		return super(SettingsView, self).form_valid(form)


class PluginView(View):
	"""
	Page to load in iframe with search results available to any ambassador
	"""

	def get(self, request, *args, **kwargs):
		username = kwargs.pop('username')
		client = check_ambassador_program(username)

		kwargs['template_name'] = 'ambassador/plugin.html'
		kwargs['embed_user'] = client.user
		response = search(request, *args, **kwargs)
		set_ambassador_cookie(response, username)
		return response
