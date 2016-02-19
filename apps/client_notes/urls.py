from django.conf.urls import patterns, url

from client_notes import views

urlpatterns = patterns('',
	url(r'^$', 'client_notes.views.home', name='notes'),

	url(r'^load_initial_data/$', views.LoadInitialData.as_view(), name='notes_load_initial_data'),

	url(r'^list_page/$', 'util.views.page_not_found', name='notes_view_notes_page'),
	url(r'^list_page/(?P<username>[\w\._-]+)/$', 'client_notes.views.home', name='notes_view_notes_page', kwargs={'action': 'list'}),
	url(r'^create_page/$', 'util.views.page_not_found', name='notes_create_note_page'),
	url(r'^create_page/(?P<username>[\w\._-]+)/$', 'client_notes.views.home', name='notes_create_note_page', kwargs={'action': 'create'}),

	url(r'^list/$', views.List.as_view(), name='notes_list'),
	url(r'^list/(?P<client_id>[0-9]+)/$', views.List.as_view(), name='notes_list'),
	url(r'^create/$', 'util.views.page_not_found', name='notes_create'),
	url(r'^create/(?P<client_id>[0-9]+)/$', views.Create.as_view(), name='notes_create'),
	url(r'^duplicate/$', 'util.views.page_not_found', name='notes_duplicate'),
	url(r'^duplicate/(?P<id>[0-9]+)/$', views.Duplicate.as_view(), name='notes_duplicate'),
	url(r'^save/$', 'util.views.page_not_found', name='notes_save'),
	url(r'^save/(?P<id>[0-9]+)/$', views.Save.as_view(), name='notes_save'),
	url(r'^get/$', 'util.views.page_not_found', name='notes_get'),
	url(r'^get/(?P<id>[0-9]+)/$', views.Get.as_view(), name='notes_get'),
	url(r'^delete/$', 'util.views.page_not_found', name='notes_delete'),
	url(r'^delete/(?P<id>[0-9]+)/$', views.Delete.as_view(), name='notes_delete'),

	url(r'^dot/$', 'util.views.page_not_found', name='notes_dot_create'),
	url(r'^dot/(?P<id>[0-9]+)/$', views.DotCreate.as_view(), name='notes_dot_create'),
	url(r'^dot/delete/$', 'util.views.page_not_found', name='notes_dot_delete'),
	url(r'^dot/delete/(?P<id>[0-9]+)/$', views.DotDelete.as_view(), name='notes_dot_delete'),

	url(r'^dot/save_position/$', 'util.views.page_not_found', name='notes_dot_save_position'),
	url(r'^dot/save_position/(?P<id>[0-9]+)/$', views.DotSavePosition.as_view(), name='notes_dot_save_position'),
	url(r'^dot/save_text/$', 'util.views.page_not_found', name='notes_dot_save_text'),
	url(r'^dot/save_text/(?P<id>[0-9]+)/$', views.DotSaveText.as_view(), name='notes_dot_save_text'),

	url(r'^save_favorite_diagram/$', 'util.views.page_not_found', name='notes_save_favorite_diagram'),
	url(r'^save_favorite_diagram/(?P<id>[0-9]+)/$', views.SaveFavoriteDiagram.as_view(), name='notes_save_favorite_diagram'),
)
