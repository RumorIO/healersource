from django.contrib.auth.models import User
from django.http import Http404
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin, ProcessFormView
from django.shortcuts import get_object_or_404, redirect

from account_hs.utils import login_user
from account_hs.authentication import user_authenticated
from healers.models import is_healer


@user_authenticated
def impersonate(request, username):
	"""Login as selected user."""
	request_user = request.user
	original_user = request.session.get('original_user', False)
	if original_user:
		if not get_object_or_404(User, username=original_user).is_superuser:
			raise Http404
	elif not request_user.is_superuser:
		raise Http404

	new_user = get_object_or_404(User, username=username)
	login_user(request, new_user)

	if not original_user:
		request.session['original_user'] = request_user.username

	elif original_user == new_user.username:
		request.session['original_user'] = None

	else:
		request.session['original_user'] = original_user

	#if original_user:
	#    if original_user != new_user.profile:
	#        request.session['original_user'] = original_user
	#elif request_user != new_user:
	#    request.session['original_user'] = request_user.profile

	if is_healer(new_user):
		return redirect('what_next')
	else:
		return redirect('home')


def page_not_found(request, **kwargs):
	raise Http404


class LoginRequiredMixin(object):
	"""
	Mixin for class based view to require login
	"""
	@classmethod
	def as_view(cls, **initkwargs):
		view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
		return user_authenticated(view)


class MultipleFormsMixin(FormMixin):
	"""
	A mixin that provides a way to show and handle several forms in a
	request.
	"""
	form_classes = {}  # set the form classes as a mapping

	def get_form_classes(self):
		return self.form_classes

	def get_form_kwargs(self, active=False):
		"""
		Returns the keyword arguments for instantiating the form.
		For active form update with POST or PUT
		"""
		kwargs = {
			'initial': self.get_initial(),
			'prefix': self.get_prefix(),
		}

		if active and self.request.method in ('POST', 'PUT'):
			kwargs.update({
				'data': self.request.POST,
				'files': self.request.FILES,
			})
		return kwargs

	def get_forms(self, form_classes, active_form_name=None):
		return dict([(key, klass(**self.get_form_kwargs(active_form_name == key)))
			for key, klass in form_classes.items()])

	def form_invalid(self, forms):
		return self.render_to_response(self.get_context_data(forms=forms))


class ProcessMultipleFormsView(ProcessFormView):
	"""
	A mixin that process one of multiple forms on POST.
	Process form for POST['form_name'] key.
	"""
	def get(self, request, *args, **kwargs):
		form_classes = self.get_form_classes()
		forms = self.get_forms(form_classes)
		return self.render_to_response(self.get_context_data(forms=forms))

	def post(self, request, *args, **kwargs):
		form_name = request.POST.get('form_name')

		form_classes = self.get_form_classes()
		forms = self.get_forms(form_classes, active_form_name=form_name)
		form = forms[form_name]

		if form.is_valid():
			return self.form_valid(form)
		else:
			forms[form_name] = form
			return self.form_invalid(forms)


class BaseMultipleFormsView(MultipleFormsMixin, ProcessMultipleFormsView):
	"""
	A base view for displaying several forms.
	"""


class MultipleFormsView(TemplateResponseMixin, BaseMultipleFormsView):
	"""
	A view for displaing several forms, and rendering a template response.
	"""
