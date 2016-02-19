from django.conf.urls import patterns, url

from account_hs.authentication import user_authenticated
from intake_forms.views import (IntakeFormAnswersList, intake_form,
	question_edit, ViewIntakeFormAnswer, intake_form_change, question_delete,
	intake_form_answer, SendIntakeForm)

urlpatterns = patterns('',
	url(r"^$", user_authenticated(IntakeFormAnswersList.as_view()), name='intake_forms_list'),

	url(r"^edit/$", intake_form, name='intake_form'),

	url(r"^edit/(?P<question_id>[0-9]+)/$",
		question_edit,
		name='intake_form_question_edit'),

	url(r"^answer/healers/(?P<healer>[\w\._-]+)/clients/(?P<client>[\w\._-]+)/$",
		user_authenticated(ViewIntakeFormAnswer.as_view()),
		name='view_intake_form_answer'),

	url(r"^answer/healers/$", 'util.views.page_not_found',
		name='view_intake_form_answer'),

	url(r"^change/$", intake_form_change, name='intake_form_change'),

	url(r"^delete/(?P<question_id>[0-9]+)/$",
		question_delete,
		name='intake_form_question_delete'),

	url(r"^send/$", SendIntakeForm.as_view(), name="send_intake_form"),

	url(r"^(?P<username>[\w\._-]+)/$",
		intake_form_answer,
		name='intake_form_answer'),
)
