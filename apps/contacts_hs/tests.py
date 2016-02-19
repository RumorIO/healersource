import os
import io

from django.core.urlresolvers import reverse
from healers.tests import HealersTest
from contacts_hs.views import is_valid_email, get_csv_contacts


class CsvClientImportTest(HealersTest):
	def get_file_path(self, filename):
		BASE_DIR = os.path.dirname(os.path.dirname(__file__))
		return BASE_DIR + '/contacts_hs/tests_files/' + filename

	def import_clients(self, filename):
		filepath = self.get_file_path(filename)
		with open(filepath, 'rU') as _file:
			return self.client.post(reverse('import_csv_contacts'), {'csv': _file}, follow=True)

	def get_clients_data(self, clients):
		clients_data = []
		for client in clients:
			c = {
				'first name': client.first_name,
				'last name': client.last_name,
				'email': client.email,
				'phone': client.contact_phone,
			}
			clients_data.append(c)
		return clients_data

	def client_import_test(self, filename):
		def read_csv():
			def process_contact(contact):
				def get_contact_email(email):
					# emails get converted to lowerstrings or ignored if it's not valid.
					if is_valid_email(email):
						return email.lower()
					else:
						return ''

				if contact['first name'] == '':
					return

				for key, value in contact.iteritems():
					# strings become unicode if not ''
					if value != '':
						contact[key] = unicode(value, 'utf-8')
				contact['email'] = get_contact_email(contact['email'])
				return contact

			filepath = self.get_file_path(filename)
			with open(filepath, 'rU') as _file:
				_file = io.StringIO(unicode(_file.read(), 'utf-8'), newline=None)
				contacts = get_csv_contacts(_file)
				output_contacts = []
				for contact in contacts:
					contact = process_contact(contact)
					if contact is not None:
						output_contacts.append(contact)
				return output_contacts

		response = self.import_clients(filename)
		self.assertRedirects(response, reverse('friends', args=['clients']), 302, 200)
		clients_data = self.get_clients_data(response.context['friends'])
		original_data = read_csv()

		# sort lists
		clients_data.sort()
		original_data.sort()

		self.assertEqual(clients_data, original_data)

	def test_normal(self):
		self.client_import_test('clients_normal.csv')

	def test_more_than_4_columns(self):
		self.client_import_test('clients_more_than_4.csv')

	def test_different_delimiter(self):
		self.client_import_test('clients_different_delimiter.csv')

	def test_less_than_3_columns(self):
		response = self.import_clients('clients_less_than_3_columns.csv')
		self.assertEqual(response.status_code, 200)
		self.assertIn('The CSV file contains less than 3 columns.', response.content)

	def test_ignore_empty_first_name(self):
		response = self.import_clients('clients_normal.csv')
		clients_data = self.get_clients_data(response.context['friends'])
		self.assertEqual(len(clients_data), 4)

	def test_empty_file(self):
		response = self.import_clients('empty.csv')
		self.assertEqual(response.status_code, 200)
		self.assertIn('Could not determine delimiter', response.content)

	def test_remove_first_row_if_not_valid_email(self):
		response = self.import_clients('clients_not_valid_email_in_first_row.csv')
		clients_data = self.get_clients_data(response.context['friends'])
		self.assertEqual(len(clients_data), 3)

	def test_ignore_clients_if_emails_exist_already(self):
		response = self.import_clients('clients_normal.csv')
		clients_data = self.get_clients_data(response.context['friends'])

		self.assertEqual(len(clients_data), 4)

		response = self.import_clients('clients_normal.csv')
		clients_data = self.get_clients_data(response.context['friends'])

		# It becomes 5 because one of the clients doesn't have an email address.
		self.assertEqual(len(clients_data), 5)
