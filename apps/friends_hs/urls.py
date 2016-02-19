from django.conf.urls import patterns, url
#from healers.forms import ClientsIpSearchForm

urlpatterns = patterns("",

	url(r"^$", "healers.views.friends", name="friends"),

	url(r'^export/$', 'about.views.all_users', name='clients_export', kwargs={'center_clients_only': 'True'}),

#	url(r"^search/$", "healers.views.friends_search", name="friends_search"),
#	url(r"^geosearch/$", "healers.views.friends_search", name="friends_geosearch", kwargs={"form_class": ClientsIpSearchForm}),
	url(r"^invite/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_invite", kwargs={"action": "invite"}),

	url(r"^accept/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_accept", kwargs={"action": "accept"}),
	url(r"^decline/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_decline", kwargs={"action": "decline"}),

	url(r"^remove/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_remove", kwargs={"action": "remove"}),
	url(r"^remove_referral/(?P<user_id>[0-9]+)/(?P<refers_to>[0-9]+)$", "healers.views.friend_process", name="friend_remove_referral", kwargs={"action": "remove_referral"}),

	url(r"^approve/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_approve", kwargs={"action": "approve"}),
	url(r"^add/(?P<user_id>[0-9]+)$", "healers.views.friend_process", name="friend_add", kwargs={"action": "add"}),

)
