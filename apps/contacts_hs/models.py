from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models

from friends.models import Contact

import requests

GOOGLE_API = 0
FACEBOOK_API = 1

API_CHOICES = (
	(GOOGLE_API, 'Google'),
	(FACEBOOK_API, 'Facebook'),
)

STATUS_RUNNING = 0
STATUS_DONE = 1
STATUS_FAIL = 2

STATUS_CHOICES = (
	(STATUS_RUNNING, 'Running'),
	(STATUS_DONE, 'Done'),
	(STATUS_FAIL, 'Fail'),
)

class ContactsImportStatus(models.Model):
	user = models.ForeignKey(User)
	api = models.PositiveSmallIntegerField(choices=API_CHOICES)
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES)
	contacts_count = models.PositiveIntegerField(default=0)

	def is_running(self):
		return self.status == STATUS_RUNNING

	def message(self):
		message = ''
		if self.status == STATUS_RUNNING:
			if self.contacts_count > 0:
				message = "<blink>Working...</blink> Imported %d Contacts from %s" % (self.contacts_count, self.get_api_display())
			else:
				message = "<p>Contacting %s. Please be patient, this may take several minutes<blink>...</blink></p><p><em>You can leave this page and import will continue in the background</em></p>" % (self.get_api_display())
		if self.status == STATUS_DONE:
			message = "All Done! Successfully Imported %d Contacts from %s" % (self.contacts_count, self.get_api_display())
		if self.status == STATUS_FAIL:
			message = "Fail! Successfully Imported %d Contacts from %s" % (self.contacts_count, self.get_api_display())

		return message


class ContactInfo(models.Model):
	contact = models.ForeignKey(Contact, blank=True, null=True)
	client = models.ForeignKey('clients.Client', blank=True, null=True)
	healer = models.ForeignKey('healers.Healer', related_name="healer_contacts")
	first_name = models.CharField(max_length=30, blank=True)
	last_name = models.CharField(max_length=30, blank=True)
	address_line1 = models.CharField("Address Line 1", max_length=42, blank=True)
	address_line2 = models.CharField("Address Line 2", max_length=42, blank=True)
	postal_code = models.CharField("Zip Code", max_length=10, blank=True,
									db_index=True)
	city = models.CharField(max_length=42, blank=True)
	state_province = models.CharField("State", max_length=42, blank=True)
	country = models.CharField('Country', max_length=42, blank=True)

	def text(self, separator='\n', email_link=False):
		phones = self.phone_numbers.all()
		info = [unicode(phone) for phone in phones]

		for email in self.emails.all():
			if email_link:
				info.append('<a href="mailto:' + email.email + '">' + email.email + '</a>')
			else:
				info.append(email)

		if self.address_string():
			info.append('<br>')
			info.append(self.address_string())

		return separator.join(info)

	def address_string(self):
		address = ''
		if self.address_line1:
			address += self.address_line1 + '<br>'
		if self.address_line2:
			address += self.address_line2 + '<br>'
		if self.city:
			address += self.city + ', '
		if self.state_province:
			address += self.state_province + ' '
		if self.postal_code:
			address += self.postal_code
		if self.country:
			address += '<br>' + self.country

		return address


class ContactGroup(models.Model):
	name = models.CharField(max_length=255)
	contacts = models.ManyToManyField(ContactInfo, related_name="groups")
	google_id = models.CharField(max_length=255)

	def __unicode__(self):
		return self.name

class ContactPhone(models.Model):
	contact = models.ForeignKey(ContactInfo, related_name="phone_numbers")
	type = models.CharField(max_length=42, default="Mobile")
	number = models.CharField(max_length=42)

	def __unicode__(self):
		return '%s: %s' % (self.type, self.number)

class ContactEmailManager(models.Manager):
	def get_first_email(self, user):
		contact_emails = super(ContactEmailManager, self).get_queryset().filter(contact__client__user=user)
		if contact_emails:
			return contact_emails[0].email
		else:
			return None

class ContactEmail(models.Model):
	contact = models.ForeignKey(ContactInfo, related_name="emails")
	type = models.CharField(max_length=42, default="Other")
	email = models.EmailField(max_length=42)

	objects = ContactEmailManager()

	def __unicode__(self):
		return '%s: %s' % (self.type, self.email)

class ContactSocialId(models.Model):
	contact = models.ForeignKey(Contact)
	service = models.CharField(max_length=75, db_index=True)
	social_id = models.CharField(max_length=200)
	point = gis_models.PointField(spatial_index=True, null=True, blank=True)

	def __unicode__(self):
		return "%s: %s" % (self.contact.name, self.social_id)

	def fb_profile_pic(self, height=350):
		return "https://graph.facebook.com/%s/picture?height=%s" % (
			self.social_id, height
		)

	def fb_profile_url(self, final_url=False):
		url = "https://www.facebook.com/profile.php?id=%s" % self.social_id
		if not final_url:
			return url
		else:
			try:
				r = requests.get(url)
				return r.url
			except:
				return url
