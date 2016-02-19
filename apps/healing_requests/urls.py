from django.conf.urls import patterns, url

from account_hs.authentication import user_authenticated
from healing_requests.views import (
	Home, ShowHealingRequest, EditHealingRequest, DeleteHealingRequest
)

urlpatterns = patterns("healing_requests.views",
	url(r"^home$", Home.as_view(), name="healing_request_home"),
	url(r"^(?P<id>\d+)$", ShowHealingRequest.as_view(), name='show_healing_request'),
	url(r"^edit/(?P<id>\d+)$", user_authenticated(EditHealingRequest.as_view()), name='edit_healing_request'),
	# url(r"^my_requests$", MyRequestList.as_view(), name="my_healing_requests"),
	url(r"^requests/(?P<id>\d+)/delete/$", user_authenticated(DeleteHealingRequest.as_view()),
		name='delete_healing_request'),
	url(r"^search/delete/(?P<id>\d+)/$", 'delete_search', name='delete_healing_request_search'),
	url(r"^search/show/(?P<id>\d+)/$", 'show_search', name='show_healing_request_search'),
)
