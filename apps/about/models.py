from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.db.models.signals import post_save
from oauth_access.models import UserAssociation


class UserAssociationDated(models.Model):
	user_assoc = models.OneToOneField(UserAssociation, primary_key=True)
	date_created = models.DateTimeField(auto_now_add=timezone.now)


@receiver(post_save, sender=UserAssociation)
def listener(sender, instance, created, **kwargs):
	if created:
		UserAssociationDated.objects.create(user_assoc=instance)
