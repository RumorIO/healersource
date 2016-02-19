from django.db import models


class Feedback(models.Model):
	client = models.ForeignKey('clients.Client')
	text = models.TextField("text")
	date = models.DateTimeField()
