from django.conf.urls import patterns, url

from gratitude_stream import views

urlpatterns = patterns('',
	url(r'^$', 'gratitude_stream.views.home', name='gratitude_stream'),
	url(r'^post/$', 'util.views.page_not_found', name='gs_post'),
	url(r'^post/(?P<question_id>[0-9]+)/$', views.PostPost.as_view(), name='gs_post'),
	url(r'^comment/$', 'util.views.page_not_found', name='gs_comment'),
	url(r'^comment/(?P<post_id>[0-9]+)/$', views.Comment.as_view(), name='gs_comment'),
	url(r'^like/$', 'util.views.page_not_found', name='gs_like'),
	url(r'^like/(?P<posting_type>post|postcomment)/(?P<posting_id>[0-9]+)/$', views.PostLike.as_view(), name='gs_like'),
	url(r'^report/$', 'util.views.page_not_found', name='gs_report'),
	url(r'^report/(?P<posting_type>post|postcomment)/(?P<posting_id>[0-9]+)/$', views.PostReport.as_view(), name='gs_report'),
)
