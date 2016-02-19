from django.conf.urls import patterns, url

from util.constants import USERNAME_URL_PATTERN

from ambassador.views import (AmbassadorRedirectView, DashboardView,
	SettingsView, PromoView, PluginView)


urlpatterns = patterns("",
	url(r"^$",
		DashboardView.as_view(),
		name="dashboard"),
	url(r"^settings/$",
		SettingsView.as_view(),
		name="settings"),
	url(r"^promo/$",
		PromoView.as_view(),
		name="promo"),
	url(r"^{}/plugin/$".format(USERNAME_URL_PATTERN),
		PluginView.as_view(),
		name="plugin"),
	url(r"^{}/$".format(USERNAME_URL_PATTERN),
		AmbassadorRedirectView.as_view(),
		name="front_page"),
	url(r"^{}/tour/$".format(USERNAME_URL_PATTERN),
		AmbassadorRedirectView.as_view(),
		name="tour"),
	url(r"^{}/signup/$".format(USERNAME_URL_PATTERN),
		AmbassadorRedirectView.as_view(),
		name="signup"),
	url(r"^{}/signup/plugin/$".format(USERNAME_URL_PATTERN),
		AmbassadorRedirectView.as_view(),
		name="signup_plugin"),
	url(r"^{}/massage-therapist-soap-notes/$".format(USERNAME_URL_PATTERN),
		AmbassadorRedirectView.as_view(),
		name="landing_page_notes")
)
