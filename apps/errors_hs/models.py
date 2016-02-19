from django.db import models
from django.conf import settings


class ErrorReport(models.Model):
	date = models.DateTimeField(default=settings.GET_NOW())
	report = models.TextField(blank=True)
