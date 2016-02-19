from django.conf.urls import patterns, url
from healers.forms import ProviderConfirmForm
from .views import (SaveDiscountCode, LocationMap, NewClient,
					AddTreatmentTypeLength)


urlpatterns = patterns("",
	url(r"^$", "healers.views.healer_list", name="healer_list"),
	url(r"^save_discount_code/$", SaveDiscountCode.as_view(), name="save_discount_code"),
	url(r"^new_client/$", NewClient.as_view(), name="new_client"),

	url(r"^gift_certificates/$", 'healers.views.gift_certificates', name="gift_certificates"),
	url(r"^gift_certificates/redeem_certificate/(?P<code>[0-9A-Za-z]{6})", "healers.views.redeem_certificate", name="redeem_certificate"),

	url(r"^photo_edit/$", "healers.views.photo_edit", name="avatar_change"),
	url(r"^photo_edit/facebook/$", "contacts_hs.views.import_facebook_photo", name="import_facebook_photo"),
	url(r"^photo_edit/(?P<username>[\w\._-]+)/$", "healers.views.photo_edit", name="avatar_change"),

	url(r"^permission/(?P<username>[\w\._-]+)/$", "healers.views.add_wellness_center_permission", name="add_wellness_center_permission"),
	url(r"^create/$", "healers.views.create_provider", name="healer_create"),
	url(r"^confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", "pinax.apps.account.views.password_reset_from_key", name="healer_confirm",
		kwargs={'form_class': ProviderConfirmForm, 'template_name': 'account/wcenter_create_healer_set_password.html'}),

	url(r"^add_treatment_type_length/$", AddTreatmentTypeLength.as_view(), name="add_treatment_type_length"),

	url(r"^location_map/(?P<id>[0-9]+)/$", LocationMap.as_view(), name="location_map"),
	url(r"^location_map/$", 'util.views.page_not_found', name="location_map"),

	url(r"^referrals_to_me/(?P<username>[\w\._-]+)/$", "healers.views.referrals_to_me", name="referrals_to_me"),

	url(r"^healer_info/(?P<username>[\w\._-]+)/$", "healers.views.healer_info", name="healer_info"),

	url(r"^settings/change_reminder_interval/$", "healers.views.healer_change_profile_reminder_interval", name="healer_change_profile_reminder_interval"),

	# url(r"^settings/profile/content/$", "healers.views.healer_edit", name="healer_edit_content", kwargs={"template_name": "healers/settings/edit_profile_content.html"}),
	url(r"^settings/profile/$", "healers.views.healer_edit", name="healer_edit"),
	url(r"^settings/profile/(?P<username>[\w\._-]+)/$", "healers.views.healer_edit", name="healer_edit"),

	url(r"^settings/review/set_review_permission/(?P<permission>disabled|clients|everyone)$", "healers.views.set_review_permission", name="set_review_permission"),

	url(r"^settings/$", "healers.views.settings_view", name="settings"),
	url(r"^settings/schedule/$", "healers.views.schedule_settings", name="schedule_settings"),

	url(r"^settings/(?P<username>[\w\._-]+)/schedule/set_schedule_visibility/(?P<visibility>disabled|clients|everyone)$", "healers.views.set_schedule_visibility", name="set_schedule_visibility"),

	url(r"^settings/treatments/$", "healers.views.treatment_types", name="treatment_types"),
	url(r"^settings/(?P<username>[\w\._-]+)/save-wellness-center-treatment-types/$", "healers.views.save_wcenter_treatment_types", name="save_wcenter_treatment_types"),

	url(r"^settings/(?P<username>[\w\._-]+)/schedule/$", "healers.views.schedule_settings", name="schedule_settings"),
	url(r"^settings/(?P<username>[\w\._-]+)/treatments/$", "healers.views.treatment_types", name="treatment_types"),

	url(r"^settings/treatments/(?P<treatment_type_id>[0-9]+)/$", "healers.views.treatment_type_edit", name="treatment_type_edit"),


	url(r"^settings/treatments/delete/(?P<treatment_type_id>[0-9]+)/$", "healers.views.treatment_type_delete", name="treatment_type_delete"),
	url(r"^settings/treatments/default/(?P<treatment_type_id>[0-9]+)/$", "healers.views.treatment_type_default", name="treatment_type_default"),

	url(r"^settings/treatments/length/add/(?P<treatment_type_id>[0-9]+)/$", "healers.views.treatment_length_add", name="treatment_length_add"),
	url(r"^settings/treatments/length/delete/(?P<treatment_length_id>[0-9]+)/$", "healers.views.treatment_length_delete", name="treatment_length_delete"),
	url(r"^settings/treatments/length/default/(?P<treatment_length_id>[0-9]+)/$", "healers.views.treatment_length_default", name="treatment_length_default"),
	url(r"^settings/treatments/copy-my-treatment-types/$", "healers.views.copy_my_treatment_types", name="copy_my_treatment_types"),
	url(r"^settings/treatments/copy-my-treatment-types/(?P<wcenter_id>[0-9]+)/$", "healers.views.copy_my_treatment_types", name="copy_my_treatment_types"),

	url(r"^settings/locations/$", "healers.views.location", name="location"),
	url(r"^settings/locations/remote_session/on/$", "healers.views.remote_session_toggle", name="remote_session_toggle_on", kwargs={'state': True}),
	url(r"^settings/locations/remote_session/off/$", "healers.views.remote_session_toggle", name="remote_session_toggle_off", kwargs={'state': False}),

	url(r"^settings/locations/room/add/(?P<location_id>[0-9]+)/$", "healers.views.room_add", name="room_add"),
	url(r"^settings/locations/room/edit/(?P<room_id>[0-9]+)/$", "healers.views.room_edit", name="room_edit"),
	url(r"^settings/locations/room/delete/(?P<room_id>[0-9]+)/$", "healers.views.room_delete", name="room_delete"),

	url(r"^settings/locations/(?P<location_id>[0-9]+)/$", "healers.views.location_edit", name="location_edit"),
	url(r"^settings/locations/delete/(?P<location_id>[0-9]+)/$", "healers.views.location_delete", name="location_delete"),
	url(r"^settings/locations/default/(?P<location_id>[0-9]+)/$", "healers.views.location_default", name="location_set_default"),

	url(r"^settings/(?P<username>[\w\._-]+)/time_off/$", "healers.views.vacation", name="vacation"),
	url(r"^settings/time_off/$", "healers.views.vacation", name="vacation"),
	url(r"^settings/timeoff/delete/(?P<vacation_id>[0-9]+)$", "healers.views.vacation_delete", name="vacation_delete"),

	url(r"^settings/account/$", "healers.views.account", name="account"),

	url(r"^settings/payments/$", "healers.views.payments_settings_view", name="payments_settings"),

	url(r"^setup/$", "healers.views.setup", name="provider_setup_intro"),
	url(r"^setup/(?P<step>[0-9]+)$", "healers.views.setup", name="provider_setup"),

	url(r"^wcenter_request_permission/(?P<username>[\w\._-]+)/$", "healers.views.wcenter_request_permission", name="wcenter_request_permission"),

	url(r"^clients_visible_to_providers/(?P<state>enable|disable)$", "healers.views.clients_visible_to_providers", name="clients_visible_to_providers"),
#	url(r"^setup/(?P<step>photo|about|specialties|profile|location|profile_preview|import_contacts|invite)$", "healers.views.setup", name="provider_setup"),

)
