import clients
from send_healing.models import GhpSettings, HealingPersonStatus


def pad_time(time):
	return time
	# return ("0%s" % time) if (time < 10) else time


def seconds_to_h_m(seconds):
	'''
	Returns H:MM format
	'''
	if not seconds:
		return

	seconds = int(seconds)
	mins = seconds/60
	hours = mins/60
	days = hours/24

	seconds %= 60

	if mins > 59:
		mins -= hours * 60

	if hours > 23:
		hours -= days * 24

	if not mins:
		return "%s secs" % (pad_time(seconds))
	elif not hours:
		return "%s min %s secs" % (mins, pad_time(seconds))
	elif not days:
		return "%s hr %s min %s secs" % (hours, pad_time(mins), pad_time(seconds))
	else:
		return "%s days %s hr %s min %s secs" % (days, hours, pad_time(mins), pad_time(seconds))


def ghp_members():
	user_ids = GhpSettings.objects.filter(i_want_to_receive_healing=True).values_list('user', flat=True)
	members = clients.models.Client.objects.filter(user__in=user_ids).exclude(user__avatar=None)
	return members


def person_status_exists(client, status):
	return HealingPersonStatus.objects.filter(client=client, status=status).exists()


def favorites_exist(client):
	return person_status_exists(client, HealingPersonStatus.FAVORITE)


def skipped_exist(client):
	return person_status_exists(client, HealingPersonStatus.TO_SKIP)
