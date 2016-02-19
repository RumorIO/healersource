from django.db import models

from django_messages.models import Message


class UnregisteredMessage(models.Model):
	sent_at = models.DateTimeField(auto_now_add=True, blank=True)


class MessageExtra(models.Model):
	SOURCE_CHOICE_HR = 1
	SOURCE_CHOICES = (
		('Healing Requests', SOURCE_CHOICE_HR),
	)

	message = models.OneToOneField(Message)
	source = models.IntegerField(choices=SOURCE_CHOICES, null=True, blank=True)
