from dashboard.models import HealerSettings


class ReadOnlySetting(Exception):
	pass


def getsetting(item):
	try:
		s = HealerSettings.objects.get(key=item)
	except HealerSettings.DoesNotExist:
		raise AttributeError
	return s.value


def setsetting(key, value):
	try:
		s = HealerSettings.objects.get(key=key)
		if s.web_only:
			raise ReadOnlySetting
		s.value = value
		s.save()
	except HealerSettings.DoesNotExist:
		HealerSettings.objects.create(key=key, value=value)
