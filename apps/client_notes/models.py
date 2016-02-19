from datetime import datetime, timedelta

from django.conf import settings
from django.db import models

from encrypted_fields import EncryptedCharField

import healers
from .exceptions import NoNotesPermissionError, NoteIsAlreadyFinalizedError


class Note(models.Model):
	CREATED_DATE_FORMAT = '%m/%d/%Y'

	healer = models.ForeignKey('healers.Healer', related_name='notes')
	client = models.ForeignKey('clients.Client')
	created_date = models.DateTimeField(auto_now_add=True)
	finalized_date = models.DateTimeField(null=True, blank=True)
	subjective = EncryptedCharField(default='', max_length=1024)
	objective = EncryptedCharField(default='', max_length=1024)
	assessment = EncryptedCharField(default='', max_length=1024)
	plan = EncryptedCharField(default='', max_length=1024)
	condition = models.PositiveSmallIntegerField(null=True, blank=True)  # 0 - 10

	class Meta:
		ordering = ['-pk']

	def __unicode__(self):
		return 'Healer: %s / Client: %s / Created: %s' % (self.healer, self. client, self.created_date)

	@property
	def is_finalized(self):
		return self.finalized_date is not None

	@property
	def created_date_formated(self):
		def get_format():
			format = '%m/%d'
			if datetime.now() - self.created_date >= timedelta(days=365):
				format += '/%y'
			return format
		return self.created_date.strftime(get_format())

	def as_dict(self):
		return {
			'client_name': str(self.client),
			'created_date': self.created_date_formated,
			'created_date_full': self.created_date.strftime(Note.CREATED_DATE_FORMAT),
			'subjective': self.subjective,
			'objective': self.objective,
			'assessment': self.assessment,
			'condition': self.condition,
			'plan': self.plan,
			'is_finalized': self.is_finalized,
		}

	def get_note_prev_next_ids(self):
		def get_note_id(type):
			if type == 'prev':
				notes_filtered = notes.filter(pk__lt=self.pk)
			elif type == 'next':
				notes_filtered = notes.filter(pk__gt=self.pk).order_by('pk')
			if notes_filtered.exists():
				return notes_filtered[0].pk
		notes = Note.objects.filter(healer=self.healer, client=self.client)
		notes_prev = get_note_id('prev')
		notes_next = get_note_id('next')
		return notes_prev, notes_next

	def get_dots(self):
		return {dot.pk: {
			'diagram_id': dot.diagram.pk,
			'marker_id': dot.marker.pk,
			'position': [dot.position_x, dot.position_y],
			'text': dot.text,
		} for dot in self.dots.all()}

	def duplicate(self):
		def duplicate_note():
			note = self
			note.pk = None
			note.created_date = None
			note.finalized_date = None
			note.save()
			return note

		def duplicate_dots():
			for dot in original_dots:
				dot.pk = None
				dot.note = note
				dot.save()

		original_dots = self.dots.all()
		note = duplicate_note()
		duplicate_dots()
		return note.pk

	def finalize(self):
		if self.is_finalized:
			raise NoteIsAlreadyFinalizedError()
		else:
			self.finalized_date = datetime.now()
			self.save(True)

	def save(self, force=False, *args, **kwargs):
		if (self.pk is None and
			not self.healer.user.has_perm(healers.models.Healer.NOTES_PERMISSION) and
				(Note.objects.filter(healer=self.healer).count() >=
					settings.NUMBER_OF_FREE_NOTES)):
			raise NoNotesPermissionError()

		if not force and self.is_finalized:
			raise NoteIsAlreadyFinalizedError()
		super(Note, self).save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		if self.is_finalized:
			raise NoteIsAlreadyFinalizedError()
		super(Note, self).delete(*args, **kwargs)


class Marker(models.Model):
	color = models.CharField(max_length=7, null=True, blank=True)
	image = models.CharField(max_length=50, null=True, blank=True)
	name = models.CharField(max_length=50)

	def __unicode__(self):
		return self.name


class Section(models.Model):
	name = models.CharField(max_length=50)
	code_name = models.CharField(max_length=50, unique=True)

	def __unicode__(self):
		return self.name


class Diagram(models.Model):
	section = models.ForeignKey(Section)
	code_name = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=50)
	order = models.PositiveSmallIntegerField()

	class Meta:
		ordering = ['order']

	def __unicode__(self):
		return self.name


class Dot(models.Model):
	note = models.ForeignKey(Note, related_name='dots')
	diagram = models.ForeignKey(Diagram, related_name='diagrams')
	marker = models.ForeignKey(Marker, related_name='markers')
	position_x = models.PositiveSmallIntegerField()
	position_y = models.PositiveSmallIntegerField()
	text = EncryptedCharField(default='', max_length=1024)

	def __unicode__(self):
		return ('Note - %s / Diagram - %s / Marker - %s - %s' %
			(str(self.note), self.diagram, self.marker, self.text))

	def save(self, *args, **kwargs):
		if self.note.is_finalized:
			raise NoteIsAlreadyFinalizedError()
		super(Dot, self).save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		if self.note.is_finalized:
			raise NoteIsAlreadyFinalizedError()
		super(Dot, self).delete(*args, **kwargs)


class FavoriteDiagram(models.Model):
	healer = models.ForeignKey('healers.Healer')
	diagrams = models.ManyToManyField(Diagram, blank=True, null=True)
