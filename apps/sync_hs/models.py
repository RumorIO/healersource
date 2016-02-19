from django.contrib.auth.models import User
from django.db import models

GOOGLE_API = 0

API_CHOICES = (
	(GOOGLE_API, 'Google'),
)

STATUS_WAITING = 0
STATUS_RUNNING = 1
STATUS_FAIL = 2

STATUS_CHOICES = (
	(STATUS_WAITING, 'Waiting'),
	(STATUS_RUNNING, 'Running'),
	(STATUS_FAIL, 'Fail'),
)

ACTION_NEW = 0
ACTION_UPDATE = 1
ACTION_DELETE = 2

ACTION_CHOICES = (
	(ACTION_NEW, 'New'),
	(ACTION_UPDATE, 'Update'),
	(ACTION_DELETE, 'Delete')
)


class CalendarSyncStatusManager(models.Manager):

	def start(self, user, api):
		self.create(user=user, api=api)

	def stop(self, user, api):
		self.filter(user=user, api=api).delete()

	def is_running(self, user, api):
		return self.filter(user=user, api=api).count() > 0


class CalendarSyncStatus(models.Model):

	user = models.ForeignKey(User)
	api = models.PositiveSmallIntegerField(choices=API_CHOICES)

	objects = CalendarSyncStatusManager()


class CalendarSyncQueueManager(models.Manager):

	def add(self, appointment, action, wcenter=None):
		def delete_tasks_for_appt():
			tasks = self.filter(appointment=appointment, wellness_center=wcenter)
			tasks.exclude(status=STATUS_RUNNING).delete()

		if action == ACTION_DELETE:
			# if appointment was not created yet, remove tasks, no need for deleting tasks
			if self.filter(appointment=appointment, wellness_center=wcenter, action=ACTION_NEW).exclude(status=STATUS_RUNNING):
				self.filter(appointment=appointment, wellness_center=wcenter).delete()
				return
			delete_tasks_for_appt()
		if action == ACTION_UPDATE:
			# if appointment was not created yet, replace tasks
			if self.filter(appointment=appointment, wellness_center=wcenter, action=ACTION_NEW).exclude(status=STATUS_RUNNING):
				action = ACTION_NEW
			delete_tasks_for_appt()
		task = CalendarSyncQueueTask()
		task.appointment = appointment
		task.action = action
		task.api = GOOGLE_API
		if wcenter is not None:
			task.wellness_center = wcenter
		task.save()


class CalendarSyncQueueTask(models.Model):

	MAX_ATTEMPTS = 10

	appointment = models.ForeignKey("healers.Appointment")
	wellness_center = models.ForeignKey('healers.WellnessCenter', null=True,
		default=None)
	api = models.PositiveSmallIntegerField(choices=API_CHOICES)
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0)
	action = models.PositiveSmallIntegerField(choices=ACTION_CHOICES)
	attempts = models.PositiveIntegerField(default=0)

	objects = CalendarSyncQueueManager()

	class Meta:
		ordering = ['id']

	def __unicode__(self):
		title = '%s: %s' % (self.appointment, self.action)
		if self.wellness_center is not None:
			title = '%s - %s' % (self.wellness_center, title)
		return title

	@classmethod
	def get_object_name(cls, is_wcenter=False):
		if is_wcenter:
			return 'wellness_center'
		else:
			return 'appointment__healer'


class UnavailableCalendar(models.Model):
	"""
	Calendar with unavailable slots
	"""
	healer = models.ForeignKey("healers.Healer")
	api = models.PositiveSmallIntegerField(choices=API_CHOICES)
	calendar_id = models.CharField(max_length=1024)
	title = models.CharField(max_length=1024, blank=True)
	update_date = models.DateTimeField(blank=True, null=True)

	def __unicode__(self):
		return '%s - %s' % (self.healer, self.title)
