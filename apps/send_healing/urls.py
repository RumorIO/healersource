from django.conf.urls import patterns, url

from util.constants import USERNAME_URL_PATTERN

from send_healing import views

urlpatterns = patterns("send_healing.views",
	url(r"^$", 'home', name="send_healing"),
	url(r"^facebook/$", "facebook_healing", name="send_healing_facebook"),
	url(r"^facebook/associate_new_account/$", "facebook_healing", kwargs={'associate_new_account': True},
		name="send_healing_facebook_associate_new_account"),

	url(r"^load_initial_data/$", views.LoadInitialData.as_view(), name="send_healing_ajax_load_initial_data"),
	url(r"^history/$", views.History.as_view(), name="send_healing_ajax_history"),
	url(r"^total_healing_sent/$", views.TotalHealingSent.as_view(), name="send_healing_ajax_total_healing_sent"),
	url(r"^list/(?P<type>skipped|favorite)/$", views.List.as_view(), name="send_healing_ajax_list"),
	url(r"^remove_status/(?P<type>skipped|favorite)/(?P<id>[0-9]+)/$", views.RemoveStatus.as_view(), name="send_healing_ajax_remove_status"),
	url(r"^add_favorite/(?P<type>client|contact)/(?P<id>[0-9]+)/$", views.AddFavorite.as_view(), name="send_healing_ajax_add_favorite"),
	url(r"^settings/save/$", views.SaveSettings.as_view(), name="send_healing_ajax_save_settings"),
	url(r"^settings/load/$", views.LoadSettings.as_view(), name="send_healing_ajax_load_settings"),
	url(r"^send_healing_to_person/{}/$".format(USERNAME_URL_PATTERN), "send_healing_to_person", name="send_healing_to_person"),
	url(r"^send_healing_to_person/$", views.SendHealingToPerson.as_view(), name="send_healing_ajax_send_healing_to_person"),
)

urlpatterns += patterns('',
	url(r"^remove_status/(?P<type>skipped|favorite)/$", 'util.views.page_not_found', name="send_healing_ajax_remove_status"),
	url(r"^add_favorite/$", 'util.views.page_not_found', name="send_healing_ajax_add_favorite")
)
