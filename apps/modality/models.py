import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.gis.db import models as gis_models

import healers
import modality


class ModalityCategory(models.Model):
	title = models.CharField(max_length=64, blank=True, default='')

	objects = gis_models.GeoManager()

	def __unicode__(self):
		return self.title

	def save(self, *args, **kwargs):
		super(ModalityCategory, self).save(*args, **kwargs)
		try:
			save_modality_menu()
		except Exception:
			pass


class ModalityManager(gis_models.GeoManager):
	def get_queryset(self):
		return super(ModalityManager, self).get_queryset().filter(approved=True)

	def get_with_unapproved(self, healer):
		return super(ModalityManager, self).get_queryset()\
			.filter(Q(approved=True) | Q(added_by=healer))


class Modality(models.Model):
	category = models.ManyToManyField(ModalityCategory)
	title = models.CharField(max_length=64, blank=True, default='')
	description = models.TextField(default='', blank=True)
	visible = models.BooleanField(default=True, db_index=True)

	healer = models.ManyToManyField('healers.Healer')
	added_by = models.ForeignKey('healers.Healer', blank=True,
									null=True, related_name='added_modality')
	approved = models.BooleanField(default=True, db_index=True)
	rejected = models.BooleanField(default=False, db_index=True)

	objects = gis_models.GeoManager()
	objects_approved = ModalityManager()

	def __unicode__(self):
		return self.title

	def first_letter(self):
		if self.title:
			return self.title[0]
		else:
			return ''

	def save(self, *args, **kwargs):
		if self.approved:
			self.rejected = False
		if self.rejected:
			self.approved = False
		super(Modality, self).save(*args, **kwargs)
		try:
			save_modality_menu()
		except Exception:
			pass


def save_modality_menu():
	"""
		Save modalities which have providers as html to file
	"""
	menu = []
	menu.append('<ul id="modality_menu" class="menu">')
	menu.append('<li>')
	menu.append('<ul>')
	menu.append('<li><a href="#" onclick="setModality(\'\', \'\', \'\')"><i>Any Specialty</i></a></li>')

	tmpl = '<li><span>%s</span><a href="#" onclick="setModality(%s, \'%s\', %s)"><span>%s</span>%s</a>'
	tmpl_modality = '<a data-fb-options="type:ajax width:800" class="modality_link floatbox nav_specialties" href="%s"></a>'
	categories = ModalityCategory.objects.filter(modality__healer__isnull=False).order_by('title').distinct()
	for category in categories:
		menu.append(tmpl % ('', category.id, category, 'true', '>', category))
		modalities = category.modality_set.filter(healer__isnull=False).order_by('title').distinct()
		if modalities:
			menu.append('<ul>')
			for modality in modalities:
				link = (tmpl_modality % reverse('modality_description', args=[modality.id]))
				menu.append(tmpl % (link, modality.id, modality, 'false', '', modality))
				menu.append('</li>')
			menu.append('</ul>')
		menu.append('</li>')
	other_modalities = Modality.objects_approved\
		.filter(category__isnull=True, healer__isnull=False)\
		.order_by('title').distinct()
	if other_modalities:
		menu.append('<li><a href="#"><span>></span>Other</a>')
		menu.append('<ul>')
		for modality in other_modalities:
			link = (tmpl_modality % reverse('modality_description', args=[modality.id]))
			menu.append(tmpl % (link, modality.id, modality, 'false', '', modality))
		menu.append('</ul>')
		menu.append('</li>')
	menu.append(('<li><a href="%s"><i>Browse All Specialties</i></a></li>') % reverse('modailty_list'))
	menu.append('</ul>')
	menu.append('</li>')
	menu.append('</ul>')

	dir = os.path.split(settings.MODALITY_MENU_PATH)[0]
	if not os.path.exists(dir):
		os.makedirs(dir)
	fp = open(settings.MODALITY_MENU_PATH, "w+")
	fp.writelines(menu)
	fp.close()

	return "\n".join(menu)


def get_modality_menu():
	"""
	Read modality menu from file or generate it if can't read
	"""
	modality_menu = ""

	try:
		fp = open(settings.MODALITY_MENU_PATH, 'r')
		modality_menu = fp.read()
		fp.close()
	except Exception:
		try:
			modality_menu = save_modality_menu()
		except Exception:
			modality_menu = ""

	return modality_menu


@receiver(m2m_changed, sender=Modality.healer.through)
def modality_changed_signal(action, model, **kwargs):
	def update_default_modality(healer):
		modalities = healer.modality_set.all()
		if len(modalities) > 0:
			healer.default_modality = modalities[0].title
			healer.save()

	if action in ['post_add', 'post_remove', 'post_clear'] and not kwargs['reverse']:
		if type(kwargs['instance']) == modality.models.Modality:
			if kwargs['pk_set'] is not None:
				healers_ = model.objects.filter(pk__in=kwargs['pk_set'])
				for healer in healers_:
					update_default_modality(healer)
		elif type(kwargs['instance']) == healers.models.Healer:
			healer = kwargs['instance']
			update_default_modality(healer)
