from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db import models

from dashboard.services.mail_sender import MailSender
import clients
import send_healing


class SentHealing(clients.models.PersonAbstract):
	sent_by = models.ForeignKey('clients.Client', related_name='sent_healing')
	started_at = models.DateTimeField(null=True, blank=True)
	ended_at = models.DateTimeField(null=True, blank=True)
	duration = models.IntegerField(default=0)
	skipped = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return u"%s" % self.duration

	@classmethod
	def total_healing_sent(cls):
		seconds = sum(cls.objects.all().values_list(
			"duration", flat=True))
		return send_healing.utils.seconds_to_h_m(seconds)

	@classmethod
	def total_healing_sent_to_num_people(cls, sent_by=None):
		def count_content_type_objects(content_type):
			qset = cls.objects.filter(person_content_type=content_type)
			if sent_by is not None:
				qset = qset.filter(sent_by=sent_by)
			return qset.distinct('person_object_id').count()

		client_content_type = ContentType.objects.get(app_label='clients', model='client')
		contact_content_type = ContentType.objects.get(app_label='friends', model='contact')
		return (count_content_type_objects(contact_content_type) +
			count_content_type_objects(client_content_type))

	def healing_sent(self):
		return send_healing.utils.seconds_to_h_m(self.duration)

	def save(self, *args, **kwargs):
		if (self.pk is None and
				self.type() == 'client' and
				self.person.ghp_notification_frequency == 'every time'):
			mailsender = MailSender('ghp_every_time', self.person.user, healers=[self.sent_by])
			mailsender.send_emails()
		super(SentHealing, self).save(*args, **kwargs)


class GhpSettings(models.Model):
	user = models.OneToOneField(User, related_name='ghp_settings')
	send_to_ghp_members = models.BooleanField(default=False)
	send_to_my_fb_friends = models.BooleanField(default=False)
	send_to_my_favorites_only = models.BooleanField(default=False)
	i_want_to_receive_healing = models.BooleanField(default=False)
	urgent = models.BooleanField(default=False)


class HealingPersonStatus(clients.models.PersonAbstract):
	NORMAL = 0
	FAVORITE = 1
	TO_SKIP = 2
	STATUSES = (
		(NORMAL, 'Normal'),
		(FAVORITE, 'Favorite'),
		(TO_SKIP, 'To skip')
	)

	client = models.ForeignKey('clients.Client')
	status = models.PositiveSmallIntegerField(default=NORMAL, choices=STATUSES)


class Phrase(models.Model):
	text = models.CharField(max_length=1024)
