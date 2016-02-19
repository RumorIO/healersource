from django.conf.urls import patterns, url

from .views import ImportContactsStatus, CheckImportStatus

urlpatterns = patterns("",
	url(r"^import/google/$", "contacts_hs.views.import_google_contacts", name="import_google_contacts"),
	url(r"^import/csv/$", "contacts_hs.views.import_csv_contacts", name="import_csv_contacts"),
	url(r"^import/facebook/$", "contacts_hs.views.import_facebook_contacts", name="import_facebook_contacts"),
	url(r"^import/status/$", ImportContactsStatus.as_view(), name="import_contacts_status"),
	url(r"^import/status/check$", CheckImportStatus.as_view(), name="import_status_check"),

	url(r"^delete/(?P<contact_id>[0-9]+)/(?P<redirect>referrals|clients)/$", "contacts_hs.views.delete_contact", name="delete_contact"),
)
