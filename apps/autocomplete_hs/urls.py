from django.conf.urls import patterns, url
from .views import (AutocompleteClientsWithNotes, AutocompleteContacts,
	AutocompleteCity, AutocompleteModality, AutocompleteGeoName)

urlpatterns = patterns("autocomplete_hs.views",
	url(r"^first_last/$",
		"autocomplete_friends_first_or_last",
		name="autocomplete_friends_first_or_last"),

	url(r"^search_name_or_email/$",
		"autocomplete_search_name_or_email",
		name="autocomplete_search_name_or_email"),

	url(r"^search_name_or_email_delete_account/$",
		"autocomplete_search_name_or_email",
		name="autocomplete_search_name_delete_account",
		kwargs={'delete_account': True}),

	url(r"^search_name_or_email_add_friend/$",
		"autocomplete_search_name_or_email",
		name="autocomplete_search_name_or_email_add_friend",
		kwargs={'show_add_friend_links': True}),

	url(r"^search_name_or_email_username/$",
		"autocomplete_search_name_or_email",
		name="autocomplete_search_name_or_email_add_friend",
		kwargs={'return_username': True}),

	url(r"^modality/$",
		AutocompleteModality.as_view(),
		name="autocomplete_modality"),

	url(r"^modality_and_category/$",
		"autocomplete_modality_or_category",
		name="autocomplete_modality_or_category"),

	url(r"^client_first_last/$",
		"autocomplete_client_first_or_last",
		name="autocomplete_client_first_or_last"),

	url(r'^city/$', AutocompleteCity.as_view(), name='autocomplete_city'),
	url(r'^contacts/$', AutocompleteContacts.as_view(), name='autocomplete_contacts'),
	url(r'^clients_with_notes/$', AutocompleteClientsWithNotes.as_view(), name='autocomplete_clients_with_notes'),
	url(r'^geoname/$', AutocompleteGeoName.as_view(), name='autocomplete_geoname'),

	url(r"^providers/$",
		"autocomplete_providers",
		name="autocomplete_providers"),

)
