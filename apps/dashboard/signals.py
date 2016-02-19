# coding=utf-8
from django.db.models.signals import post_save
from django.dispatch import receiver

from emailconfirmation.models import EmailAddress
from dashboard import EMAIL_VERIFIED
from dashboard.utils import create_action, get_action


@receiver(post_save, sender=EmailAddress)
def email_verified(sender, instance, created, **kwargs):
	if created:
		verifications = EmailAddress.objects.filter(
			user=instance.user,
			verified=True,
			primary=True
		)
		if len(verifications) > 0:
			verifications_flags = get_action(EMAIL_VERIFIED, instance.user)
			if len(verifications_flags) == 0:
				create_action(EMAIL_VERIFIED, instance.user)
