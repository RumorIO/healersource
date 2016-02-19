import json
from datetime import datetime

from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework.response import Response

from account_hs.authentication import user_authenticated
from autocomplete_hs.views import autocomplete_all_clients
from healers.forms import NewUserForm
from healers.views import HealerAuthenticated
from clients.models import Client
from phonegap.utils import render_page

from .models import Marker, Diagram, Section, FavoriteDiagram, Note, Dot
from .exceptions import NoNotesPermissionError, NoteIsAlreadyFinalizedError


class NotesView(HealerAuthenticated):
	client = None

	def get_initial_data(self, client_id):
		super(NotesView, self).get_initial_data()
		if client_id is not None:
			self.client = get_object_or_404(Client, pk=client_id)


class NotesEdit(HealerAuthenticated):
	def get_initial_data(self, id):
		super(NotesEdit, self).get_initial_data()
		self.note = get_object_or_404(Note, healer=self.healer, pk=id)


class DotEdit(HealerAuthenticated):
	def get_initial_data(self, id):
		super(DotEdit, self).get_initial_data()
		self.dot = get_object_or_404(Dot, note__healer=self.healer, pk=id)


def render_notes_home(extra_context, request=None):
	template = 'client_notes/home.html'
	context = {
		'new_user_form': NewUserForm(),  # new client
		'markers': Marker.objects.all().order_by('id'),
		'diagrams': Diagram.objects.all().order_by('section', 'order'),
		'sections': Section.objects.all()
	}
	return render_page(request, template, context, extra_context)


@user_authenticated
def home(request, username=None, action=None):
	client_id = client_name = None
	if username is not None:
		client = get_object_or_404(Client, user__username=username)
		client_id = client.pk
		client_name = unicode(client)

	def call_api_view(view_class):
		return view_class.as_view()(request, format='json').render().content

	extra_context = {
		'action': action,
		'client_id': client_id,
		'client_name': client_name,
		'initial_data': call_api_view(LoadInitialData),
		'notes_list': call_api_view(List)
	}
	return render_notes_home(extra_context, request)


class LoadInitialData(HealerAuthenticated):
	def get(self, request, format=None):
		def get_favorite_diagrams():
			favorite_diagram = FavoriteDiagram.objects.get_or_create(healer=self.healer)[0]
			favorite_diagrams = favorite_diagram.diagrams
			if not favorite_diagrams.exists():
				favorite_diagrams.add(*settings.NOTES_DEFAULT_FAVORITE_DIAGRAMS)

			return list(favorite_diagrams.all().values_list('pk', flat=True))

		def get_current_client():
			client = self.healer.get_current_appointment_client()
			if client is not None:
				return {'name': unicode(client), 'id': client.pk}

		self.get_initial_data()
		data = {
			'clients': json.loads(autocomplete_all_clients(request)),
			'favorite_diagrams': get_favorite_diagrams(),
			'current_client': get_current_client(),
		}
		return Response(data)


class List(NotesView):
	def get(self, request, client_id=None, format=None):
		self.get_initial_data(client_id)
		notes = self.healer.notes.all()
		if self.client is not None:
			notes = notes.filter(client=self.client)
		notes_exist = notes.exists()
		complete_forms = self.healer.completed_forms()
		if notes_exist:
			if 'is_mobile' in request.GET:
				is_mobile = json.loads(request.GET.get('is_mobile'))
			else:
				is_mobile = request.is_mobile
			html = render_to_string('client_notes/notes.html',
				{'notes': notes,
				'client_filter': self.client is not None,
				'is_mobile': is_mobile,
				'complete_forms': complete_forms,
				'healer_username': self.healer.user.username})
		else:
			html = 'No notes yet.'
		return Response({'html': html, 'notes_exist': notes_exist})


class Create(NotesView):
	def post(self, request, client_id, format=None):
		self.get_initial_data(client_id)
		try:
			output = Note.objects.create(healer=self.healer, client=self.client).pk
		except NoNotesPermissionError:
			output = {'error_type': 'no_notes_permission'}
		return Response(output)


class Duplicate(NotesEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)
		try:
			output = self.note.duplicate()
		except NoNotesPermissionError:
			output = {'error_type': 'no_notes_permission'}
		return Response(output)


def process_note_change_request(function, **kwargs):
	try:
		return function(**kwargs)
	except NoteIsAlreadyFinalizedError:
		return Response({'ajax_error': 'Note is already finalized.'})


class Save(NotesEdit):
	def post(self, request, id, format=None):
		def get_function():
			if json.loads(request.POST['finalize']):
				return note.finalize
			return note.save

		self.get_initial_data(id)
		note = self.note
		note.objective = request.POST['objective']
		note.subjective = request.POST['subjective']
		note.assessment = request.POST['assessment']
		note.plan = request.POST['plan']
		note.condition = request.POST.get('condition', None)

		created_date = request.POST.get('created_date', None)
		if created_date:
			created_date = datetime.strptime(
				created_date, Note.CREATED_DATE_FORMAT).date()
			if note.created_date.date() != created_date:
				note.created_date = created_date

		result = process_note_change_request(get_function())
		if type(result) == Response:
			return result
		return Response()


class Get(NotesEdit):
	def get(self, request, id, format=None):
		self.get_initial_data(id)
		prev_note, next_note = self.note.get_note_prev_next_ids()
		return Response({
			'note': self.note.as_dict(),
			'dots': self.note.get_dots(),
			'prev_note': prev_note,
			'next_note': next_note,
		})


class Delete(NotesEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)

		result = process_note_change_request(self.note.delete)
		if type(result) == Response:
			return result
		return Response()


class DotCreate(NotesEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)
		position = json.loads(request.POST['position'])
		diagram = Diagram.objects.get(pk=request.POST['diagram_id'])
		marker = Marker.objects.filter(pk=request.POST['marker_id'])
		if marker:
			marker = marker[0]
		else:
			marker = Marker.objects.all()[0]
		text = request.POST['text']

		dot = process_note_change_request(Dot.objects.create, **{
			'note': self.note,
			'diagram': diagram,
			'marker': marker,
			'text': text,
			'position_x': position[0],
			'position_y': position[1]
		})
		if type(dot) == Response:
			return dot
		return Response(dot.pk)


class DotDelete(DotEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)
		result = process_note_change_request(self.dot.delete)
		if type(result) == Response:
			return result
		return Response()


class DotSavePosition(DotEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)
		position = json.loads(request.POST['position'])
		self.dot.position_x = position[0]
		self.dot.position_y = position[1]
		result = process_note_change_request(self.dot.save)
		if type(result) == Response:
			return result
		return Response()


class DotSaveText(DotEdit):
	def post(self, request, id, format=None):
		self.get_initial_data(id)
		self.dot.text = request.POST['text']
		result = process_note_change_request(self.dot.save)
		if type(result) == Response:
			return result
		return Response()


class SaveFavoriteDiagram(HealerAuthenticated):
	"""Add diagram if action is True and remove it if it's false."""

	def post(self, request, id, format=None):
		self.get_initial_data()
		favorite_diagrams = FavoriteDiagram.objects.get(
			healer=self.healer).diagrams
		if json.loads(request.POST['action']):
			favorite_diagrams.add(id)
		else:
			favorite_diagrams.remove(id)
		return Response(list(favorite_diagrams.all().values_list('pk', flat=True)))
