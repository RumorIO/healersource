from django.contrib.contenttypes.models import ContentType
from dashboard.models import HealerActions


#TODO: Managers?


def create_action(action, obj):
	return HealerActions.objects.create(
		action=action,
		object_id=obj.pk,
		content_type_id=ContentType.objects.get_for_model(obj).pk
	)


def get_action(action, obj):
	return HealerActions.objects.filter(
		action=action,
		object_id=obj.pk,
		content_type_id=ContentType.objects.get_for_model(obj).pk
	)
