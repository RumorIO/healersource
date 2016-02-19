from django import forms
from intake_forms.models import *
from intake_forms import mail_healer_after_intake_form_answered


class ChangeIntakeForm(forms.ModelForm):

	class Meta:
		model = IntakeForm
		fields = ['answer_option']
		widgets = {
			'answer_option': forms.RadioSelect()
		}


class QuestionForm(forms.ModelForm):
	text = forms.CharField(label="Question", widget=forms.Textarea(attrs={'style': 'width: 98%; height: 69px;'}))
	is_required = forms.ChoiceField(label='',
		widget=forms.RadioSelect(),
		choices=((True, 'Client is required to answer this question'),
				(False, 'Answer is optional')), initial=True)

	class Meta:
		model = Question
		fields = ['text', 'answer_rows', 'is_required']


class IntakeFormAnswerForm(forms.Form):
	"""Form to answer intake questions."""

	def __init__(self, *args, **kwargs):
		self.client = kwargs.pop('client')
		self.intake_form = kwargs.pop('intake_form')
		super(IntakeFormAnswerForm, self).__init__(*args, **kwargs)
		answer = None
		_answer_text = None
		try:
			answer = self.intake_form.answer_set.get(client=self.client)
			self.fields['id'] = forms.CharField(label='Id', initial=answer.id,
				widget=forms.HiddenInput())
		except Answer.DoesNotExist:
			answer = None
		for question in self.intake_form.questions.all().order_by('id'):
			if answer:
				try:
					_answer = question.results.get(answer=answer)
					_answer_text = _answer.text
				except AnswerResult.DoesNotExist:
					_answer_text = None

			self.fields['answer_' + str(question.id)] = forms.CharField(
				label=question.text_with_optional_message, initial=_answer_text,
				required=question.is_required,
				widget=forms.Textarea(attrs={'rows': question.answer_rows}))

	def save(self):
		answer = Answer()
		send_email = False
		if self.cleaned_data.get('id', None):
			answer = Answer.objects.get(id=self.cleaned_data['id'])
		else:
			send_email = True
			answer.client = self.client
			answer.form = self.intake_form
		# answer.date=settings.GET_NOW()
		answer.save()
		for question in self.intake_form.questions.all():
			_answer_result, created = AnswerResult.objects.get_or_create(
				answer=answer,
				question=question,
				defaults={
					'text': self.cleaned_data['answer_' + str(question.id)]
				}

			)
			if not created:
				_answer_result.text = self.cleaned_data['answer_' + str(question.id)]
				_answer_result.save()

		if send_email:
			mail_healer_after_intake_form_answered(self.client, self.intake_form.healer)
