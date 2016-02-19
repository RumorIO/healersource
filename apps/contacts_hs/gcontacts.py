from sync_hs.google import GoogleDataClient
from gdata.contacts.client import ContactsClient, ContactsQuery


class GoogleContacts(GoogleDataClient):
	""" Google contacts management """

	def __init__(self, user):
		self.client = ContactsClient(source='anonymous')
		super(GoogleContacts, self).__init__(user)

	def get_groups(self):
		results = []
		entries = []
		query = ContactsQuery()
		query.max_results = 100
		query.start_index = 1

		feed = self.client.GetGroups(q=query)
		entries.extend(feed.entry)
		next_link = feed.GetNextLink()

		while next_link:
			query.start_index += 100
			feed = self.client.GetGroups(q=query)
			entries.extend(feed.entry)
			next_link = feed.GetNextLink()

		for entry in entries:
			results.append({'google_id': entry.id.text, 'name': entry.title.text})

		return results

	def get(self):
		results = []
		entries = []

		query = ContactsQuery()
		query.max_results = 100
		query.start_index = 1

		feed = self.client.GetContacts(q=query)
		entries.extend(feed.entry)
		next_link = feed.GetNextLink()

		while next_link:
			query.start_index += 100
			feed = self.client.GetContacts(q=query)
			entries.extend(feed.entry)
			next_link = feed.GetNextLink()

		for entry in entries:
			if entry.email:
				result = {'id': entry.get_id(),
							'name': entry.title.text,
							'emails': [],
							'phones': [],
							'groups': []}
				if entry.name:
					if entry.name.given_name:
						result['first_name'] = entry.name.given_name.text
					if entry.name.family_name:
						result['last_name'] = entry.name.family_name.text
				for email in entry.email:
					if email.primary == 'true':
						result['primary_email'] = email.address.lower()
					result['emails'].append(
						(email.address.lower(), email.rel.split('#')[1] if email.rel else 'Unknown'))

				for phone in entry.phone_number:
					result['phones'].append((phone.text, phone.rel.split('#')[1] if phone.rel else 'Unknown'))

				for group in entry.group_membership_info:
					result['groups'].append(group.href)

				results.append(result)

		return results
