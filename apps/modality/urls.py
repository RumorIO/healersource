from django.conf.urls import patterns, url

from modality import views

urlpatterns = patterns(
	'modality.views',
	url(r'^$', 'modality_list', name='modailty_list'),
	url(r'^add/$', 'modality_add', name='modality_add'),
	url(r'^add/(?P<username>[\w\._-]+)/$', 'modality_add', name='modality_add'),
	url(r'^get/(?P<category_id>[0-9]+|all|other)/$', views.GetModalities.as_view(), name='modality_get'),
	url(r'^healer/add/(?P<modality_id>[0-9]+)/$', views.AddHealer.as_view(), name='modality_add_healer'),
	url(r'^healer/remove/(?P<modality_id>[0-9]+)/$', views.RemoveHealer.as_view(), name='modality_remove_healer'),
	url(r'^update/(?P<modality_id>[0-9]+)/$', views.Update.as_view(), name='modality_update'),
	url(r'^category/add/$', views.AddCategory.as_view(), name='modality_add_category'),
	url(r'^category/remove/$', views.RemoveCategory.as_view(), name='modality_remove_category'),
	url(r'^category/add/(?P<modality_id>[0-9]+)/(?P<category_id>[0-9]+)/$', views.AddCategory.as_view()),
	url(r'^category/remove/(?P<modality_id>[0-9]+)/(?P<category_id>[0-9]+)/$', views.RemoveCategory.as_view()),
	url(r'^description_popup/(?P<modality_id>[0-9]+)/$', 'modality_description',
		name='modality_description'),
	url(r'^description/(?P<modality_id>[0-9]+)/$', 'modality_description',
		name='modality_description_full_page',
		kwargs={"full_page": True}),
	url(r'^providers/(?P<modality_id>[0-9]+)/$', 'modality_providers',
		name='modality_providers'),
	url(r'^providers/(?P<modality_id>[0-9]+)/(?P<zipcode>[0-9]+)/$', 'modality_providers',
		name='modality_providers_zipcode'),
	url(r'^approve/(?P<modality_id>[0-9]+)/$', 'modality_approve',
		name='modality_approve'),
	url(r'^reject/(?P<modality_id>[0-9]+)/$', 'modality_reject',
		name='modality_reject'),
	url(r"^remove/(?P<modality_id>[0-9]+)/$",
		"modality_remove",
		name="modality_remove"),
)


urlpatterns += patterns('',
	url(r'^get/$', 'util.views.page_not_found', name='modality_get'),
	url(r'^update/$', 'util.views.page_not_found', name='modality_update'),
	url(r'^healer/add/', 'util.views.page_not_found', name='modality_add_healer'),
	url(r'^healer/remove/$', 'util.views.page_not_found', name='modality_remove_healer'),
)
