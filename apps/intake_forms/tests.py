from django import test
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from healers.models import Healer, Clients
from clients.models import Client
from intake_forms.models import *
from intake_forms.forms import *


class IntakeFormTest(test.TestCase):
	fixtures = ['hs_auth.json', 'client.json', 'healers.json']

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_healer = Healer.objects.get(pk=1)
		self.test_healer.user.set_password('test')
		self.test_healer.user.save()
		result_login = self.client.login(
			email=self.test_healer.user.email,
			password='test')
		self.assertTrue(result_login)


class IntakeFormViewTest(IntakeFormTest):

	def test_get(self):
		intake_form = G(IntakeForm, healer=self.test_healer)
		response = self.client.get(reverse('intake_form'))

		self.assertEqual(intake_form, response.context['intake_form'])

	def test_add_question_post(self):
		intake_form = G(IntakeForm, healer=self.test_healer)
		data = {
			'text': 'text',
			'answer_rows': 3,
			'is_required': 'True',
		}
		self.client.post(reverse('intake_form'), data)

		question = intake_form.questions.all()[0]
		self.assertEqual(question.text, data['text'])
		self.assertEqual(question.answer_rows, data['answer_rows'])


class IntakeFormAnswerViewTest(IntakeFormTest):

	def setUp(self):
		# get client from fixture, update user password and make login
		self.test_healer = Healer.objects.get(pk=1)
		self.test_client = Client.objects.get(pk=5)
		self.test_client.user.set_password('test')
		self.test_client.user.save()
		result_login = self.client.login(
			email=self.test_client.user.email,
			password='test')
		self.assertTrue(result_login)

	def test_get_wrong_client(self):
		G(IntakeForm, healer=self.test_healer)
		response = self.client.get(
			reverse(
				'intake_form_answer',
				args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 404)

	def test_get(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		G(IntakeForm, healer=self.test_healer)
		response = self.client.get(
			reverse(
				'intake_form_answer',
				args=[self.test_healer.user.username]))

		self.assertEqual(response.status_code, 200)

	def create_form_and_answer(self):
		Clients.objects.create(from_user=self.test_healer.user, to_user=self.test_client.user)
		self.intake_form = G(IntakeForm, healer=self.test_healer)
		self.question1 = G(Question, form=self.intake_form)
		self.question2 = G(Question, form=self.intake_form)
		data = {
			'answer_' + str(self.question1.id): 'answer1',
			'answer_' + str(self.question2.id): 'answer2'
		}
		self.client.post(
			reverse(
				'intake_form_answer',
				args=[self.test_healer.user.username]),
			data)

	def test_post(self):
		self.create_form_and_answer()
		answer = Answer.objects.get(client=self.test_client)
		self.assertEqual(answer.form, self.intake_form)
		answer_result = AnswerResult.objects.get(
			answer=answer, question=self.question1)
		self.assertEqual(answer_result.text, 'answer1')
		answer_result = AnswerResult.objects.get(
			answer=answer, question=self.question2)
		self.assertEqual(answer_result.text, 'answer2')

	def test_post_if_healer_has_added_new_question(self):
		self.create_form_and_answer()
		# add new question to form
		G(Question, form=self.intake_form)
		self.client.get(
			reverse(
				'view_intake_form_answer',
				args=[self.test_healer.user.username, self.test_client.user.username]))


class IntakeFormChangeViewTest(IntakeFormTest):

	def test_new_post(self):
		response = self.client.post(
			reverse('intake_form_change'),
			{'answer_option': 1},
			follow=True)

		intake_form = response.context['intake_form']
		self.assertEqual(intake_form.healer, self.test_healer)
		self.assertEqual(intake_form.answer_option, 1)

	def test_update_post(self):
		G(IntakeForm, healer=self.test_healer, answer_option=1)
		response = self.client.post(
			reverse('intake_form_change'),
			{'answer_option': 2},
			follow=True)

		intake_form = response.context['intake_form']
		self.assertEqual(intake_form.healer, self.test_healer)
		self.assertEqual(intake_form.answer_option, 2)


class QuestionEditViewTest(IntakeFormTest):

	def test_permission(self):
		intake_form = G(IntakeForm)
		question = G(Question, form=intake_form)

		response = self.client.get(
			reverse('intake_form_question_edit', args=[question.id]))

		self.assertEqual(response.status_code, 404)

	def test_get(self):
		intake_form = G(IntakeForm, healer=self.test_healer)
		question = G(Question, form=intake_form)

		response = self.client.get(
			reverse('intake_form_question_edit', args=[question.id]))

		self.assertEqual(type(response.context['form']), QuestionForm)

	def test_post(self):
		intake_form = G(IntakeForm, healer=self.test_healer)
		question = G(Question, form=intake_form)

		data = {'text': 'test1', 'answer_rows': 5, 'is_required': 'True'}

		self.client.post(
			reverse('intake_form_question_edit', args=[question.id]),
			data)

		question = Question.objects.get(id=question.id)
		self.assertEqual(question.text, data['text'])
		self.assertEqual(question.answer_rows, data['answer_rows'])


class QuestionDeleteViewTest(IntakeFormTest):

	def test_delete(self):
		intake_form = G(IntakeForm, healer=self.test_healer)
		question = G(Question, form=intake_form)

		response = self.client.get(
			reverse('intake_form_question_delete', args=[question.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Question.objects.filter(id=question.id).count())

	def test_permission(self):
		intake_form = G(IntakeForm)
		question = G(Question, form=intake_form)

		response = self.client.get(
			reverse('intake_form_question_delete', args=[question.id]))

		self.assertEqual(response.status_code, 404)
		self.assertTrue(Question.objects.filter(id=question.id).count())
