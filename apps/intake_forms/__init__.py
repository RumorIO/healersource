from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.conf import settings
from util import full_url


def view_intake_form_answer_context(**kwargs):
	context = kwargs.get('context', {})
	from clients.models import Client
	from healers.models import Healer
	client = Client.objects.get(user__username=kwargs['client'])
	healer = Healer.objects.get(user__username=kwargs['healer'])
	questions = healer.intake_forms.all()[0].questions.all()
	qa = []
	for question in questions:
		temp = {}
		temp['question'] = question.text
		temp['answer'] = ''
		answers = question.results.filter(answer__client_id=client.id)
		if answers.exists():
			temp['answer'] = answers[0].text
		qa.append(temp)
	context['qa'] = qa
	context['client'] = client
	return context


def mail_healer_after_intake_form_answered(client, healer):
	inbox_link = render_to_string("email_link.html", {'link': full_url(reverse('messages_inbox'))})
	schedule_link = render_to_string("email_link.html", {'link': full_url(reverse('schedule'))})

	subject = render_to_string("intake_forms/emails/send_healer_after_intake_form_subject.html", client)

	context = view_intake_form_answer_context(**{
		'healer': healer.user.username,
		'client': client.user.username,
	})

	context.update({
		'inbox_link': inbox_link,
		'schedule_link': schedule_link,
		'client': unicode(client)
	})

	from healers.utils import send_hs_mail
	send_hs_mail(subject, 'intake_forms/emails/send_healer_after_intake_form_body.txt',
		context, settings.DEFAULT_FROM_EMAIL, [healer.user.email])
