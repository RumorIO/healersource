__author__ = 'daniel'

import mailchimp

from django.contrib.sites.models import Site
from django.contrib.gis.db.models.query import GeoQuerySet
from django.conf import settings
from django.core import mail
from django_yubin.models import QueuedMessage

from healing_requests.constants import HR_STATUS_DELETE


class SoftDeletionQuerySet(GeoQuerySet):
	def delete(self):
		# Bulk delete bypasses individual objects' delete methods.
		return super(SoftDeletionQuerySet, self).update(status=HR_STATUS_DELETE)

	def hard_delete(self):
		return super(SoftDeletionQuerySet, self).delete()

	def alive(self):
		return self.exclude(status=HR_STATUS_DELETE)

	def dead(self):
		return self.filter(status=HR_STATUS_DELETE)


def m2m_search(model_class, related_name, ids, queryset=None):
	''' Get queryset which contains all of the ids '''
	if queryset is None:
		queryset = model_class.objects.all()
	for _id in ids:
		queryset = queryset.filter(**{'%s__id' % related_name: _id})
	return queryset


def m2m_search_any(model_class, related_name, ids, queryset=None):
	''' Get queryset which contains any of the ids '''
	if queryset is None:
		queryset = model_class.objects.all()
	return queryset.filter(**{'%s__in' % related_name: ids})


def string_to_boolean(keys, data):
	# 'True', 'False' strings
	for key in keys:
		if key in data:
			data[key] = True if data[key].lower() == 'true' else False
	return data


def match_objects(keys, obj1, obj2):
	for key in keys:
		if getattr(obj1, key) != getattr(obj2, key):
			return False
	return True


def get_or_none(model, **kwargs):
	try:
		return model.objects.get(**kwargs)
	except model.DoesNotExist:
		return None


def full_url(path=""):
	domain = Site.objects.get_current().domain
	return "{}{}".format(domain, path)


def absolute_url(path=""):
	scheme = getattr(settings, 'DEFAULT_HTTP_PROTOCOL', 'http')
	return "{}://{}".format(scheme, full_url(path))


def starting_letters(full_name):
	return "".join([x[0].upper() for x in full_name.split(" ")])


def queryset_mix(q1, q2, queryset, operator='or'):
	if q1 is not None and q2 is not None:
		if operator == 'or':
			return q1 | q2
		elif operator == 'and':
			return q1 & q2
	elif q1 is not None:
		return q1
	elif q2 is not None:
		return q2
	else:
		return queryset


def is_correct_image_file_type(file_type, name=''):
	name = name.lower()
	return (file_type in settings.ALLOWED_IMAGE_UPLOAD_TYPES or
		(len(name) > 3 and name[-4] == '.' and name[-3:] in settings.ALLOWED_IMAGE_UPLOAD_TYPES) or
		name.endswith('.jpeg'))


def add_to_mailchimp(list_id, email, data=None):
	mc = mailchimp.Mailchimp(settings.MAILCHIMP_KEY)

	try:
		return mc.lists.subscribe(
			list_id,
			{'email': email},
			data,
			None, False)

	except mailchimp.ListAlreadySubscribedError:
		return False


def utm_tracking(func):
	def decorated_func(request, *args, **kwargs):
		if request.method == 'GET':
			for parameter in settings.UTM_TRACKING_PARAMETERS:
				if parameter in request.GET:
					request.session[parameter] = request.GET[parameter]
		result = func(request, *args, **kwargs)
		return result

	return decorated_func


def get_errors(form):
	error_elements = []
	error_list = ''
	errors = ''
	error_list_pg_bc = ''
	sorted_errors = sorted(form.errors)
	for error_field in sorted_errors:
		if error_field == '__all__':
			errors += form.errors[error_field][0] + '<br><br>'
		else:
			label = unicode(form.fields[error_field].label)
			if not label:
				label = ' '.join([word.capitalize() for word in error_field.split('_')])
			error_list += '<li>{}: {}</li>'.format(label, form.errors[error_field])
			if error_field == 'msg_security_verification':
					error_field += '_1'
			error_elements.append(error_field)

	if error_elements:
		error_list_pg_bc = errors + error_list  # error_list_pg_bc for pg backward compatibility
		errors += '<ul>{}</ul>'.format(error_list)

	return errors, error_elements, error_list_pg_bc


def get_name(name):
	if not name:
		return '', ''
	name = name.partition(' ')
	first_name = name[0]
	last_name = name[2]
	return first_name, last_name


if "django_yubin" in settings.INSTALLED_APPS and not settings.RUNNING_LOCAL:
	def get_email(index=0):
		message = QueuedMessage.objects.order_by('date_queued')[index].message
		return mail.EmailMessage(message.subject, message.encoded_message, message.from_address, [message.to_address])

	def count_emails():
		return QueuedMessage.objects.all().count()
else:
	def get_email(index=0):
		return mail.outbox[index]

	def count_emails():
		return len(mail.outbox)
