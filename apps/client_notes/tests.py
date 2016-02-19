from django import test
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G

from clients.models import Client
from healers.models import Healer
from client_notes.models import Note


class NotesTest(test.TestCase):

    def setUp(self):
        self.test_healer = G(Healer)
        self.test_client = G(Client)

        self.test_healer.user.set_password('test')
        self.test_healer.user.save()

        result_login = self.client.login(
            email=self.test_healer.user.email,
            password='test')
        self.assertTrue(result_login)


class SaveNoteTest(NotesTest):

    def create_note(self):
        return G(
            Note,
            healer=self.test_healer,
            client=self.test_client,
            finalized_date=None)

    def get_post_data(self):
        return {
            'objective': 'objective',
            'subjective': 'subjective',
            'assessment': 'assessment',
            'plan': 'plan',
            'condition': 10,
            'finalize': 'false',
            'created_date': '07/01/2015'
        }

    def test_save_all_fields(self):
        note = self.create_note()
        data = self.get_post_data()
        response = self.client.post(reverse('notes_save', args=[note.id]), data)

        self.assertEqual(response.status_code, 200)

        updated_note = Note.objects.get(id=note.id)
        self.assertEqual(updated_note.objective, data['objective'])
        self.assertEqual(updated_note.subjective, data['subjective'])
        self.assertEqual(updated_note.assessment, data['assessment'])
        self.assertEqual(updated_note.plan, data['plan'])
        self.assertEqual(updated_note.condition, data['condition'])
        self.assertEqual(updated_note.condition, data['condition'])
        self.assertEqual(
            updated_note.created_date.strftime('%m/%d/%Y'),
            data['created_date'])

    def test_save_no_created_date(self):
        note = self.create_note()
        data = self.get_post_data()
        data['created_date'] = ''
        response = self.client.post(reverse('notes_save', args=[note.id]), data)

        self.assertEqual(response.status_code, 200)

        updated_note = Note.objects.get(id=note.id)
        self.assertEqual(updated_note.created_date, note.created_date)

    def test_save_created_date_not_changed(self):
        note = self.create_note()
        data = self.get_post_data()
        data['created_date'] = note.created_date.strftime('%m/%d/%Y')
        response = self.client.post(reverse('notes_save', args=[note.id]), data)

        self.assertEqual(response.status_code, 200)

        updated_note = Note.objects.get(id=note.id)
        self.assertEqual(updated_note.created_date, note.created_date)
