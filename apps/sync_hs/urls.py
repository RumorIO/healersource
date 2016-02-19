from django.conf.urls import patterns, url

from sync_hs.views import Sync, HardReset, SoftReset

urlpatterns = patterns("",
	url(r"^$", "sync_hs.views.google_calendar_instruction", name="google_calendar_instruction"),
	url(r"^google/$", "sync_hs.views.google_calendar_sync", name="google_calendar_sync"),
	url(r"^google/run$", "sync_hs.views.google_calendar_sync", name="google_calendar_sync_run", kwargs={"run": True}),
	url(r"^google/hard_reset$", HardReset.as_view(), name="google_calendar_hard_reset"),
	url(r"^google/soft_reset$", SoftReset.as_view(), name="google_calendar_soft_reset"),
	url(r"^google/sync$", Sync.as_view(), name="google_calendar_run_sync"),
	url(r"^google/disable/$", "sync_hs.views.google_calendar_disable", name="google_calendar_disable"),
	url(r"^google/change/$", "sync_hs.views.google_calendar_disable", name="google_calendar_change", kwargs={"change": True}),
)
