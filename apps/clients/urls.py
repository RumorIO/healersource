from django.conf.urls import patterns, url

from account_hs.forms import HealerSignupForm, ClientSignupForm
from clients.views import GallerySetVisibility, SendReferral

urlpatterns = patterns("",
	url(r'^signup/validate/client/$', 'ajax_validation.views.validate', {'form_class': ClientSignupForm}, name='signup_client_validate'),
	url(r'^signup/validate/provider/$', 'ajax_validation.views.validate', {'form_class': HealerSignupForm}, name='signup_provider_validate'),  # required for pg backward compatibility
	url(r"^locations/(?P<location_id>[0-9]+)/$", "clients.views.location_edit", name="client_location_edit"),
	url(r"^client_detail/(?P<client_username>[\w\._-]+)/$", "clients.views.client_detail", name="client_detail"),
	url(r"^location_detail/(?P<appointment_id>[0-9]+)/$", "clients.views.location_detail", name="location_detail"),
	url(r"^profile/$", "clients.views.profile_edit", name="clients_profile"),

	url(r"^profile/phones/$", "clients.views.phones", name="edit_phones"),
	url(r"^profile/email/$", "clients.views.email", name="edit_email"),
	url(r"^profile/email/resend_to_user/$", "clients.views.resend_confirmation", name="resend_confirmation_to_user"),
	url(r"^profile/email/(?P<username>[\w\._-]+)/$", "clients.views.email", name="edit_email"),
	url(r"^profile/email/resend/(?P<confirmation_key>\w+)/$", "clients.views.resend_confirmation", name="resend_confirmation"),
	url(r"^profile/email/resend_to_user/(?P<username>[\w\._-]+)/$", "clients.views.resend_confirmation", name="resend_confirmation_to_user"),
	url(r"^profile/save_ghp_notification_frequency_setting/(?P<frequency>every time|daily|weekly|unsubscribe)$", "clients.views.save_ghp_notification_frequency_setting", name="save_ghp_notification_frequency_setting"),

	url(r"^videos/$", "clients.views.videos", name="videos"),
	url(r"^videos/import/$", "clients.views.videos_import", name="videos_import"),
	url(r"^videos/(?P<video_id>\d+)/remove/$", "clients.views.video_remove", name="video_remove"),
	url(r"^gallery/(?P<id>\d+)/remove/$", "clients.views.gallery_remove", name="gallery_remove"),
	url(r"^gallery/(?P<id>\d+)/rotate/(?P<direction>left|right)/$", "clients.views.gallery_rotate", name="gallery_rotate"),
	url(r"^gallery/(?P<id>\d+)/set_visibility/$", GallerySetVisibility.as_view(), name="gallery_set_visibility"),
	url(r'^gallery/$', 'django.views.defaults.page_not_found', name='gallery'),
	url(r"^gallery/change_order/$", "clients.views.gallery_order", name="gallery_change_order"),

	url(r"^send_referral/$", SendReferral.as_view(), name="send_referral"),

	url(r"^(?P<username>[\w\._-]+)/$", "clients.views.client", name="client_public_profile"),
	url(r"^select_type/(?P<service>\w+)/$", "clients.views.select_account_type", name="select_account_type"),

	url(r"^oauth/error/$", "clients.views.oauth_error", name="oauth_error"),
	url(r"^oauth/close/$", "clients.views.oauth_window_close", name="oauth_window_close"),
	url(r"^contact/(?P<client_username>[\w\._-]+)/$", "clients.views.contact_form", name="edit_contact"),

	url(r"^referral_dlg/(?P<username>[\w\._-]+)/(?P<client_or_healer>client|healer)", "clients.views.refer_dlg", name="referral_dlg"),
)
