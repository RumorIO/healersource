from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from clients.models import Client
from healers.models import Healer, ClientInvitation
from healers.utils import get_full_url


class Review(models.Model):
	RATING_CHOICES = (
		(5, '5 Stars'),
		(4, '4 Stars'),
		(3, '3 Stars'),
		(2, '2 Stars'),
		(1, '1 Star')
	)

	reviewer = models.ForeignKey(Client)
	healer = models.ForeignKey(Healer, related_name='reviews')
	title = models.CharField(max_length=255)
	review = models.TextField()
	rating = models.PositiveSmallIntegerField(
		choices=RATING_CHOICES, blank=False, default=5)
	date = models.DateTimeField(auto_now_add=True)
	reply = models.TextField(blank=True)
	reply_date = models.DateTimeField(blank=True, null=True)
	reply_visible = models.BooleanField(default=False)

	def __unicode__(self):
		return self.title

	def notify(self):
		ctx = {
			'review': self,
			'is_need_client_approval': ClientInvitation.objects.filter(
				from_user=self.reviewer.user,
				to_user=self.healer.user, status=2).count() > 0,
			'approve_url': get_full_url(
				'friend_accept', args=['clients', self.reviewer.user.id]),
			'decline_url': get_full_url(
				'friend_decline', args=['clients', self.reviewer.user.id])
		}

		from_email = settings.DEFAULT_FROM_EMAIL
		subject = render_to_string('review/emails/notify_subject.txt', ctx)

		from healers.utils import send_hs_mail
		send_hs_mail(subject, 'review/emails/notify_body.txt', ctx, from_email,
					 [self.healer.user.email])

	class Meta:
		ordering = ['-date']
