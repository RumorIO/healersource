__author__ = 'daniel'
from django.db.models import signals
from django_messages.models import Message
from django_messages.utils import new_message_email


signals.post_save.disconnect(new_message_email, sender=Message)
