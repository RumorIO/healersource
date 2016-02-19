from django.db import models
from django.core.exceptions import ValidationError
from encrypted_fields import EncryptedTextField


class IntakeForm(models.Model):
	"""
	Form with a series of questions to ask clients
	"""

	ANSWER_STORE_ON_SITE = 0
	ANSWER_ON_SITE_SEND_BY_EMAIL = 1
	ANSWER_BY_EMAIL = 2
	ANSWER_OPTION_CHOICES = (
		(ANSWER_BY_EMAIL,
			'Send intake form to client by email (this will send the client '
			'an email containing all questions, and they will email their '
			'responses to you)'),
		(ANSWER_ON_SITE_SEND_BY_EMAIL,
			'Client fills out intake form on HealerSource, and the responses '
			'are sent to me in an email. This will not store any of '
			'the client\'s information on HealerSource'),
		(ANSWER_STORE_ON_SITE, 'Store Intake form in HealerSource'),
	)

	healer = models.ForeignKey('healers.Healer', related_name='intake_forms')
	answer_option = models.PositiveSmallIntegerField(
		default=ANSWER_STORE_ON_SITE,
		choices=ANSWER_OPTION_CHOICES)

	created_at = models.DateTimeField(auto_now_add=True)


class Question(models.Model):
	"""
	Question for intake form
	"""

	form = models.ForeignKey(IntakeForm, related_name='questions')
	text = models.TextField()
	is_required = models.BooleanField(default=True)
	#the height of the textarea the client will be given to answer the question
	answer_rows = models.PositiveSmallIntegerField(
		default=1,
		choices=[(i, i) for i in range(1, 11)])

	def __unicode__(self):
		return self.text

	@property
	def text_with_optional_message(self):
		text = self.text
		if not self.is_required:
			text += ' (optional)'
		return text


class Answer(models.Model):
	"""Client's answer info for intake form."""
	client = models.ForeignKey('clients.Client', related_name='intake_form_answers')
	form = models.ForeignKey(IntakeForm)
	date = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		super(Answer, self).save(*args, **kwargs)


class AnswerResult(models.Model):
	"""Client's answer text."""
	answer = models.ForeignKey(Answer, related_name='results')
	question = models.ForeignKey(Question, related_name='results')
	text = EncryptedTextField(blank=True)


class IntakeFormSentHistory(models.Model):
	'''
	A record is saved whenever healer sends intake form to client
	'''
	client = models.ForeignKey('clients.Client', related_name='intake_form_sent_history_client')
	healer = models.ForeignKey('healers.Healer', related_name='intake_form_sent_history_healer')
	created_at = models.DateTimeField(auto_now_add=True)
	modified_at = models.DateTimeField(auto_now=True)
