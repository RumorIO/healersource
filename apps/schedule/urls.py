from django.conf.urls import patterns, url

urlpatterns = patterns("",

	url(r"^$", "healers.views.schedule", name="schedule"),
	url(r"^(?P<location_id>\d+)/$", "healers.views.schedule", name="schedule"),
	url(r"^enable_schedule_free_trial/$", "healers.views.enable_schedule_free_trial", name="enable_schedule_free_trial"),

	url(r"^manage_discount_codes/$", "healers.views.manage_discount_codes", name="manage_discount_codes"),
	url(r"^edit_discount_code/(?P<code_id>\d+)$", "healers.views.edit_discount_code", name="edit_discount_code"),


	url(r"^appointments/$", "healers.views.schedule", name="appointments"),
	url(r"^appointments/(?P<location_id>\d+)/$", "healers.views.schedule", name="appointments"),
	url(r"^appointments/(?P<location_id>\d+)/(?P<username>[\w\._-]+)/$", "healers.views.schedule", name="appointments"),
	url(r"^appointments/healer_cancel/(?P<appt_id>[0-9]+)$", "healers.views.appointment_cancel", name="healer_appointment_cancel"),

	url(r"^availability/$", "healers.views.schedule", name="availability", kwargs={"edit_availaibility": True}),
	url(r"^availability/(?P<location_id>\d+)/$", "healers.views.schedule", name="availability", kwargs={"edit_availaibility": True}),
	url(r"^availability/(?P<location_id>\d+)/(?P<username>[\w\._-]+)/$", "healers.views.schedule", name="availability", kwargs={"edit_availaibility": True}),
	url(r"^availability/(?P<username>[\w\._-]+)/$", "healers.views.schedule", name="availability", kwargs={"edit_availaibility": True}),

	url(r"^appointments/history/$", "healers.views.appointment_history", name="appointment_history"),
	url(r"^appointments/history/(?P<username>[\w\._-]+)/$", "healers.views.appointment_history", name="appointment_history_user"),
	url(r"^appointment/delete/(?P<id>\d+)/(?P<start>\d+)/$", "healers.views.appointment_delete", name="appointment_delete"),
	url(r"^appointment/delete/$", "django.views.defaults.page_not_found", name="appointment_delete"),

	url(r"^appointments/confirmed/$", "healers.views.confirmed_appointments", name="current_confirmed_appointments"),
	url(r"^appointments/confirmed/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$", "healers.views.confirmed_appointments", name="confirmed_appointments"),

	url(r"^appointments/confirm/(?P<appt_id>[0-9]+)/$", "healers.views.appointment_confirm", name="appointment_confirm"),
	url(r"^appointments/confirm_and_accept/(?P<appt_id>[0-9]+)/$", "healers.views.appointment_confirm", kwargs={'accept': True}, name="appointment_confirm_and_accept"),
	url(r"^appointments/confirm/all/(?P<username>[\w\._-]+)/$", "healers.views.appointment_confirm_all", name="appointment_confirm_all"),
	url(r"^appointments/wellness-center/(?P<type>confirm|decline)/$", "healers.views.appointment_wcenter_confirm_decline_all", name="appointment_wcenter_confirm_decline_all"),

	url(r"^appointments/decline/(?P<appt_id>[0-9]+)/$", "healers.views.appointment_decline", name="appointment_decline"),
	url(r"^appointments/decline/all/(?P<username>[\w\._-]+)/$", "healers.views.appointment_decline_all", name="appointment_decline_all"),
	url(r"^appointments/(?P<username>[\w\._-]+)/$", "healers.views.schedule", name="appointments"),
#	url(r"^appointments/receiving/$", "clients.views.appointments", name="receiving_appointments", kwargs={"template_name":"clients/healers_appointments.html"}),

#	url(r"^timeoff/$", "healers.views.vacation", name="vacation"),
#	url(r"^timeoff/delete/(?P<vacation_id>[0-9]+)$", "healers.views.vacation_delete", name="vacation_delete"),

	url(r"^embed/(?P<username>[\w\._-]+)/$", "healers.views.embed", name="embed"),
	url(r"^embed/(?P<username>[\w\._-]+)/full/$", "healers.views.embed", name="embed_full", kwargs={"include_name": True}),
	url(r"^embed/(?P<username>[\w\._-]+)/location/(?P<location>[\w\._-]+)/$", "healers.views.embed", name="embed"),
	url(r"^embed/(?P<username>[\w\._-]+)/preview/$", "healers.views.embed", name="embed_preview", kwargs={"preview": True}),
	url(r"^embed/(?P<center_username>[\w\._-]+)/(?P<username>[\w\._-]+)/$", "healers.views.embed", name="embed"),
	url(r"^embed/(?P<center_username>[\w\._-]+)/(?P<username>[\w\._-]+)/preview/$", "healers.views.embed", name="embed_preview", kwargs={"preview": True}),

	url(r"^enable/$", "healers.views.schedule_enable", name="schedule_enable"),
	url(r"^disable/$", "healers.views.schedule_disable", name="schedule_disable"),

	url(r"^(?P<username>[\w\._-]+)/$", "healers.views.schedule", name="schedule"),
#	url(r"^(?P<username>[\w\._-]+)/appointments.ics$", "healers.views.ical", name="healer_ical"),
)
