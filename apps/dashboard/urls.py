from django.conf.urls import patterns, url

urlpatterns = patterns(
	'dashboard.views',
	url(r'^$', 'index', name='index'),

	url(r'^settings/$', 'settings.list', name='settings_list'),
	url(r'^settings/(?P<key>[\w_-]+)/$', 'settings.edit', name='settings_edit'),

	url(r'^delete_account/$', 'delete_account', name='delete_account'),
	url(r'^mails/$', 'mails.list', name='mails_list'),
	url(r'^mails/(?P<slug>[\w_-]+)/$', 'mails.edit', name='mails_edit'),
	url(r'^unconfirmed_list/$', 'unconfirmed_list', name='unconfirmed_list'),
	url(r'^confirm_email/(?P<id>[0-9]+)/$', 'confirm_email', name='confirm_email'),
	url(r'^custom_schedule_payments_center_list/$', 'custom_schedule_payments_center_list', name='custom_schedule_payments_center_list'),
	url(r'^custom_schedule_payment_center/(?P<username>[\w\._-]+)/$', 'custom_schedule_payment_center', name='custom_schedule_payment_center'),
)

urlpatterns += patterns(
	'',
	url(r'^create_user/$', 'account_hs.views.signup',
		{'template': 'dashboard/create_user.html'}, name='create_user'),
)
