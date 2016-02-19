from django.conf import settings
from django.conf.urls import patterns, url, include
from django.http import HttpResponse
from django.views.generic import TemplateView, RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.decorators.csrf import csrf_exempt

from account_hs.forms import PasswordLengthResetPasswordKeyForm, LoginFormHS
from account_hs.views import (Signup, SignupClient, Login, UpdateLinkSource,
								FacebookSignup)
from errors_hs.views import ErrorReportView
from oauth2_hs.views import AccessTokenView
from apps.healers.views import IframeTest
from apps.phonegap.views import IsHealer, IsAdmin, Version
from apps.feedback.views import Submit
from apps.messages_hs.views import SendMessage

from sitemap import healersource_sitemap

# if settings.ENABLE_ADMIN_URLS:
# 	from django.contrib import admin
# 	admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover

dajaxice_autodiscover()

handler500 = "apps.server_error"

urlpatterns = patterns('',
	url(r'^', include('about.urls')),
	url(r'^confirmation_required/', include('about.confirmation_required_urls')),

	url(r'^massage-therapist-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes'),
	url(r'^physical-therapist-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes_pt'),
	url(r'^occupational-therapist-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes_ot'),
	url(r'^chiropractor-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes_chiropractor'),
	url(r'^chiropractors-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes_chiropractors'),
	url(r'^chiropractic-soap-notes/', 'about.views.landing_page_notes', name='landing_page_notes_chiropractic'),
	url(r'^book/thanks/$', 'about.views.book_thanks', name='book_thanks'),
	url(r'^book/', 'about.views.landing_page_book', name='landing_page_book'),

	url(r'^ambassador/', include('ambassador.urls', namespace='ambassador')),

	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),
	url(r'^oauth2login/google/', 'oauth2_hs.views.google', name='oauth2_google_login'),
	url(r'^oauth2callback/google/', 'oauth2_hs.views.auth_return'),
	url('^oauth2_facebook/access_token/?$',
		csrf_exempt(AccessTokenView.as_view()), name='access_token'),

	# phonegap links
	url(r'^version/$', Version.as_view(), name='version'),  # for backward compatibility
	url(r'^is_healer/$', IsHealer.as_view(), name='is_healer'),
	url(r'^is_admin/$', IsAdmin.as_view(), name='is_admin'),
	url(r'^phonegap/', include('phonegap.urls')),

	url(r"^facebook_signup/$", FacebookSignup.as_view(), name="ajax_facebook_signup"),

	url(r"^purchase_gift_certificate/(?P<username>[\w\._-]+)/$", "healers.views.purchase_gift_certificate", name="purchase_gift_certificate"),
	url(r"^blog/", include("blog_hs.urls")),
	url(r"^invitations/", include("friends_app.urls")),

	url(r"^submit_feedback/$", Submit.as_view(), name="submit_feedback"),
	url(r"^error_report/$", ErrorReportView.as_view(), name="error_report"),
	url(r"^send_message/$", SendMessage.as_view(), name="send_message"),

	url(r"^signup_client_ajax/$", SignupClient.as_view(), name="ajax_signup_client"),
	url(r"^login_ajax/$", Login.as_view(), name="ajax_login"),

	url(r"^signup/$", "account_hs.views.signup", name="signup"),
	url(r"^signup/plugin/$", "account_hs.views.signup", name="signup_plugin", kwargs={'plugin': True}),
	url(r"^signup_ajax/$", Signup.as_view(), name="ajax_signup"),
	url(r"^signup/thanks_verification/$", "util.views.page_not_found", name="signup_thanks"),
	url(r"^signup/thanks_verification/(?P<type>client|healer|wellness_center)/$", "account_hs.views.signup_thanks", name="signup_thanks"),
	url(r"^signup/thanks/$", "util.views.page_not_found", name="signup_thanks_no_verification"),
	url(r"^signup/thanks/(?P<type>client|healer|wellness_center)/$", "account_hs.views.signup_thanks", name="signup_thanks_no_verification", kwargs={"email_verification": False}),
	url(r'^account/update-link-source/$', UpdateLinkSource.as_view(), name='update_link_source'),
	url(r"^messages/", include("django_messages.urls")),

	url(r"^login/$", "pinax.apps.account.views.login", name="login_page", kwargs={"form_class": LoginFormHS}),
	url(r"^logout/$", "django.contrib.auth.views.logout", {"template_name": "account/logged_out.html"}, name="logout_page"),
	url(r'^captcha/', include('captcha.urls')),

	# password reset
	url(r"^password_reset/$", "clients.views.password_reset", name="acct_passwd_reset"),
	url(r"^password_reset/done/$", "pinax.apps.account.views.password_reset_done", name="acct_passwd_reset_done"),
	url(r"^password_reset_key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
		"pinax.apps.account.views.password_reset_from_key",
		{'form_class': PasswordLengthResetPasswordKeyForm},
		name="acct_passwd_reset_key"),


	url(r"^payments/", include("payments.urls")),
	url(r"^provider/", include("healers.urls")),
	url(r"^events/", include("events.urls")),
	url(r"^client/", include("clients.urls")),
	url(r"^contacts/", include("contacts_hs.urls")),
	url(r"^phonegap/", include("phonegap.urls")),

	url(r"^schedule/", include("schedule.urls")),
	url(r"^sync/", include("sync_hs.urls")),
	url(r"^notes/", include("client_notes.urls")),

	#	 url(r"^healers/$", "healers.views.friends", name="clients_healers", kwargs={"friend_type":"healers"}),
	#	 url(r"^referrals/$", "healers.views.friends", name="referrals", kwargs={"friend_type":"referrals"}),
	#	 url(r"^clients/$", "healers.views.friends", name="clients", kwargs={"friend_type":"clients"}),
	#	 url(r"^search/(?P<friend_type>referrals|clients|healers)$", "healers.views.friends_search", name="friends_search"),
	#	 url(r"^friends/$", include("friends_hs.urls")),
	# url(r"^refer/(?P<provider_username>[\w\._-]+)/clients/$", 'healers.views.clients', name="refer_clients_list"),
	# url(r"^refer/(?P<client_username>[\w\._-]+)/providers/$", 'healers.views.providers', name="refer_providers_list"),
	url(r"^refer/(?P<provider_username>[\w\._-]+)/(?P<client_username>[\w\._-]+)/client/$",
		'healers.views.refer_client',
		name="refer_from_providers"),
	url(r"^refer/(?P<provider_username>[\w\._-]+)/(?P<client_username>[\w\._-]+)/provider/$",
		'healers.views.refer_client',
		kwargs={'email_to_provider': False},
		name="refer_from_clients"),
	url(r"^(?P<friend_type>referrals|clients|healers|providers)/", include("friends_hs.urls")),
#	url(r"^invite/healers_admin/$", "friends_app.views.invite", kwargs={"invite_type": "provider"}, name="invite_healer"),
#	url(r"^home/$", "healers.views.healers_geosearch", name="home"),


	url(r"^reviews/", include("review.urls")),
	url(r"^gratitude_stream/", include("gratitude_stream.urls")),
	url(r"^appointments/$", "clients.views.appointments", name="receiving_appointments"),
	url(r"^appointments/cancel/(?P<appt_id>[0-9]+)$", "clients.views.appointment_cancel", name="appointment_cancel"),
	url(r"^appointments/reschedule/(?P<appt_id>[0-9]+)$", "clients.views.appointment_cancel", kwargs={'action': 'reschedule'}, name="appointment_reschedule"),

	url(r"^login_redirect/", "minidetector.views.login_redirect", name="login_redirect"),

	url(r"^emailconfirmation/(\w+)", "clients.views.confirm_email", name="emailconfirmation_confirm_email"),

	url(r"^oauth/", include("oauth_access.urls")),

	url(r"^autocomplete/", include("autocomplete_hs.urls")),

	url(r"^specialties/", include("modality.urls")),

	url(r'^dashboard/', include('dashboard.urls', namespace='dashboard')),

	url(r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),

	url(r"^iframe_test/$", IframeTest.as_view(), name="iframe_test"),

	url(r"^disable_reminders/", "clients.views.disable_reminders", name="disable_reminders"),

	url(r"^videos/$", "clients.views.videos_list", name="videos_list_all"),
	url(r"^videos/(?P<username>[\w\._-]+)/$", "clients.views.videos_list", name="videos_list_user"),

	url(r"^tshirt/$",
		TemplateView.as_view(template_name='about/tshirt.html'),
		name='tshirt'),

	url(r"^intake_form/", include("intake_forms.urls")),

	url(r"^messagelog/$", "clients.views.messagelog"),
	url(r"^messagelog/failures/$", "clients.views.messagelog", kwargs={"failures": True}),

	url(r"^healing_requests/", include("healing_requests.urls")),

	url(r'^impersonate/(?P<username>[\w\._-]+)/$', "util.views.impersonate", name='impersonate'),
	url(r"^delete_account/$", "account_hs.views.delete", name='delete_account'),
	url(r"^delete_account/(?P<username>[\w\._-]+)/$", "account_hs.views.delete", name='delete_account'),

	url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': healersource_sitemap}),

	#reserved urls - remove any that are < 6 chars for performance reasons
#	url(r"^blog/$", "django.views.defaults.page_not_found"),
	url(r"^reference/$", "django.views.defaults.page_not_found"),
#	url(r"^wiki/$", "django.views.defaults.page_not_found"),
#	url(r"^shop/$", "django.views.defaults.page_not_found"),
#	url(r"^store/$", "django.views.defaults.page_not_found"),
#	url(r"^info/$", "django.views.defaults.page_not_found"),
	url(r"^information/$", "django.views.defaults.page_not_found"),
#	url(r"^help/$", "django.views.defaults.page_not_found"),
	url(r"^contact/$", "django.views.defaults.page_not_found"),
#	url(r"^news/$", "django.views.defaults.page_not_found"),
#	url(r"^book/$", "django.views.defaults.page_not_found"),
	url(r"^booking/$", "django.views.defaults.page_not_found"),
	url(r"^bookings/$", "django.views.defaults.page_not_found"),
	url(r"^offers/$", "django.views.defaults.page_not_found"),
	url(r"^pricing/$", "django.views.defaults.page_not_found"),
#	url(r"^intro/$", "django.views.defaults.page_not_found"),
	url(r"^introduction/$", "django.views.defaults.page_not_found"),
#	url(r"^gift/$", "django.views.defaults.page_not_found"),
	url(r"^gift_certificate/$", "django.views.defaults.page_not_found"),
	url(r"^gift_certificates/$", "django.views.defaults.page_not_found"),
	url(r"^service/$", "django.views.defaults.page_not_found"),
	url(r"^services/$", "django.views.defaults.page_not_found"),
#	url(r"^apply/$", "django.views.defaults.page_not_found"),
#	url(r"^jobs/$", "django.views.defaults.page_not_found"),
#	url(r"^press/$", "django.views.defaults.page_not_found"),
#	url(r"^faq/$", "django.views.defaults.page_not_found"),
#	url(r"^feed/$", "django.views.defaults.page_not_found"),
#	url(r"^rss/$", "django.views.defaults.page_not_found"),
	url(r"^addons/$", "django.views.defaults.page_not_found"),
	url(r"^articles/$", "django.views.defaults.page_not_found"),
	url(r"^treatments/$", "django.views.defaults.page_not_found"),
#	url(r"^spa/$", "django.views.defaults.page_not_found"),
	url(r"^school/$", "django.views.defaults.page_not_found"),
	url(r"^schools/$", "django.views.defaults.page_not_found"),
	url(r"^calendar/$", "django.views.defaults.page_not_found"),
	url(r"^condition/$", "django.views.defaults.page_not_found"),
	url(r"^symptom/$", "django.views.defaults.page_not_found"),
	url(r"^symptoms/$", "django.views.defaults.page_not_found"),
#	url(r"^soap/$", "django.views.defaults.page_not_found"),
#	url(r"^wall/$", "django.views.defaults.page_not_found"),
	url(r"^inspiration/$", "django.views.defaults.page_not_found"),
	url(r"^inspirations/$", "django.views.defaults.page_not_found"),
	url(r"^history/$", "django.views.defaults.page_not_found"),
	url(r"^groups/$", "django.views.defaults.page_not_found"),
	url(r"^circles/$", "django.views.defaults.page_not_found"),
#	url(r"^trade/$", "django.views.defaults.page_not_found"),
	url(r"^trades/$", "django.views.defaults.page_not_found"),
	url(r"^connect/$", "django.views.defaults.page_not_found"),
	url(r"^connection/$", "django.views.defaults.page_not_found"),
	url(r"^connections/$", "django.views.defaults.page_not_found"),
	url(r"^health/$", "django.views.defaults.page_not_found"),
	url(r"^healing/$", "django.views.defaults.page_not_found"),
	url(r"^newsletter/$", "django.views.defaults.page_not_found"),
	url(r"^mailing_list/$", "django.views.defaults.page_not_found"),
	url(r"^mailing_lists/$", "django.views.defaults.page_not_found"),
	url(r"^shirts/$", "django.views.defaults.page_not_found"),
	url(r"^tshirts/$", "django.views.defaults.page_not_found"),
	url(r"^apparel/$", "django.views.defaults.page_not_found"),
	url(r"^google/$", "django.views.defaults.page_not_found"),
	url(r"^facebook/$", "django.views.defaults.page_not_found"),
	url(r"^twitter/$", "django.views.defaults.page_not_found"),
	url(r"^linkedin/$", "django.views.defaults.page_not_found"),
	url(r"^linked_in/$", "django.views.defaults.page_not_found"),
	url(r"^instagram/$", "django.views.defaults.page_not_found"),
#	url(r"^table/$", "django.views.defaults.page_not_found"),
#	url(r"^other/$", "django.views.defaults.page_not_found"),
	url(r"^empty/$", lambda request: HttpResponse(""), name="empty_page"),
	url(r"^healing-circle/", include("send_healing.urls")),
	url(r"^global_healing_project/", RedirectView.as_view(pattern_name='send_healing')),
	url(r"^(?P<username>[\w\._-]+)/$", "healers.views.healer", name="healer_my_profile"),
	url(r"^(?P<username>[\w\._-]+)/service/(?P<treatment_type>[\w\._-]+)/$", "healers.views.healer", name="healer_my_profile"),
	url(r"^(?P<username>[\w\._-]+)/(?P<location>[\w\._-]+)/$", "healers.views.healer", name="healer_public_profile"),

	url(r"^(?P<city>[\w\._-]+)/(?P<specialty>[\w\._-]+)/"
		r"(?P<username>[\w\._-]+)/$",
		"healers.views.healer", name="healer_public_profile"),

	url(r"^(?P<city>[\w\._-]+)/(?P<specialty>[\w\._-]+)/"
		r"(?P<username>[\w\._-]+)/(?P<treatment_type>[\w\._-]+)/$",
		"healers.views.healer", name="healer_public_profile"),

)

urlpatterns += staticfiles_urlpatterns()

# if settings.ENABLE_ADMIN_URLS:
# 	urlpatterns = patterns("",
# 		url(r"^admin/invite_user/$", "pinax.apps.signup_codes.views.admin_invite_user", name="admin_invite_user"),
# 		url(r"^admin/", include(admin.site.urls)),
# 	) + urlpatterns

if settings.SERVE_MEDIA:
	urlpatterns += patterns(
		'',
		# url(r'', include("staticfiles.urls")),
		(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
	)

try:
	import urls_local
	urlpatterns += urls_local.urlpatterns
except ImportError:
	urls_local = None
