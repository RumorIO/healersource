from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.views.generic.base import TemplateView
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.http import Http404

from rest_framework.response import Response

from util import get_or_none
from account_hs.authentication import user_authenticated
from healers.views import HealerAuthenticated
from healers.models import Healer, is_my_client, is_concierge
from healers.forms import NewUserForm
from clients.models import Client
from autocomplete_hs.views import autocomplete_all_clients

from intake_forms.forms import *
from intake_forms import view_intake_form_answer_context


@user_authenticated
def intake_form(request, template_name="intake_forms/intake_form.html"):
	healer = get_object_or_404(Healer, user=request.user)
	add_question_form = QuestionForm(request.POST or None)

	if(request.POST):
		intake_form, created = IntakeForm.objects.get_or_create(healer=healer)
	else:
		intake_form = get_or_none(IntakeForm, healer=healer)

	questions = None
	if intake_form:
		questions = intake_form.questions.all().order_by('id')
		if add_question_form.is_valid():
			question = add_question_form.save(commit=False)
			question.form = intake_form
			question.save()

	return render_to_response(template_name, {
		'intake_form': intake_form,
		'questions': questions,
		# 'change_intake_form': change_intake_form,
		'add_question_form': add_question_form
	}, context_instance=RequestContext(request))


@user_authenticated
def intake_form_change(request):
	if not request.POST:
		return redirect('intake_form')

	healer = get_object_or_404(Healer, user=request.user)

	try:
		intake_form = IntakeForm.objects.get(healer__user=request.user)
	except IntakeForm.DoesNotExist:
		intake_form = None

	change_intake_form = ChangeIntakeForm(
		request.POST,
		instance=intake_form)

	if change_intake_form.is_valid():
		intake_form = change_intake_form.save(commit=False)
		intake_form.healer = healer
		intake_form.save()

	return redirect('intake_form')


def intake_form_answer(request, username):
	if not request.user.is_authenticated():
		return redirect('login_page')

	healer = get_object_or_404(Healer, user__username=username)
	if not is_my_client(healer.user, request.user):
		raise Http404
	intake_form = get_object_or_404(IntakeForm, healer=healer)

	form = IntakeFormAnswerForm(
		request.POST or None,
		client=request.user.client,
		intake_form=intake_form)

	success = False
	if form.is_valid():
		form.save()
		success = True
		if request.session.pop('concierge_request', False):
			return redirect(reverse('concierge_thanks', args=[username]))

	return render_to_response("intake_forms/answer.html", {
		'is_concierge': is_concierge(healer),
		'healer_name': unicode(healer.user.client),
		'form': form,
		'success': success
	}, context_instance=RequestContext(request))


# @user_authenticated
# def intake_form_answer_success(request):
# 	return render_to_response("intake_forms/answer_success.html", {
# 	}, context_instance=RequestContext(request))


@user_authenticated
def question_edit(request, question_id):
	question = get_object_or_404(
		Question,
		id=question_id,
		form__healer__user=request.user)

	form = QuestionForm(request.POST or None, instance=question)
	if form.is_valid():
		form.save()
		return redirect('intake_form')

	return render_to_response("intake_forms/question_edit.html", {
		'form': form
	}, context_instance=RequestContext(request))


@user_authenticated
def question_delete(request, question_id):
	question = get_object_or_404(
		Question,
		id=question_id,
		form__healer__user=request.user)
	question.delete()
	return redirect('intake_form')


class SendIntakeForm(HealerAuthenticated):
	def post(self, request, format=None):
		try:
			client = get_object_or_404(Client, id=request.POST['client_id'])
		except:
			return HttpResponseBadRequest()
		self.get_initial_data()
		self.healer.send_intake_form(client)
		return Response()


class ViewIntakeFormAnswer(TemplateView):
	template_name = "intake_forms/view_intake_form_answer.html"

	def get_context_data(self, **kwargs):
		context = super(ViewIntakeFormAnswer, self).get_context_data(**kwargs)
		kwargs['context'] = context
		context = view_intake_form_answer_context(**kwargs)
		return context


class IntakeFormAnswersList(TemplateView):
	template_name = "intake_forms/intake_form_answer_list.html"

	def get_context_data(self, **kwargs):
		context = super(IntakeFormAnswersList, self).get_context_data(**kwargs)
		healer = Healer.objects.get(user=self.request.user)
		context['complete_forms'] = healer.completed_forms()
		context['incomplete_forms'] = healer.incomplete_forms()
		context['healer'] = healer
		context['clients'] = autocomplete_all_clients(self.request)
		context['new_user_form'] = NewUserForm()
		return context

	def dispatch(self, request, *args, **kwargs):
		try:
			IntakeForm.objects.get(healer__user=request.user)

		except IntakeForm.DoesNotExist:
			return redirect('intake_form')

		return super(IntakeFormAnswersList, self).dispatch(request, *args, **kwargs)
