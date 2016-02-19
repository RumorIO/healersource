from django.conf.urls import patterns, url

from account_hs.authentication import user_authenticated
from .views import (HistoryView, StripeConnectPayments, MarkUnpaid, MarkPaid,
	Charge, SaveCard, ClientAppointments, SaveAccountSettings)


urlpatterns = patterns(
	'payments.views',
	url(r'^$', 'stripe_connect_payments', name='stripe_connect_payments'),

	url(r'^save/account_settings$', SaveAccountSettings.as_view(), name='payments_save_account_settings'),
	url(r'^save/card$', SaveCard.as_view(), name='payments_save_card'),
	url(r'^remove/card$', 'remove_card', name='payments_remove_card'),
	url(r'^history/$',
		user_authenticated(HistoryView.as_view()),
		name='payments_history'),

	url(r'^stripe_connect/load/$', StripeConnectPayments.as_view(), name='stripe_connect_load_payments'),
	url(r'^stripe_connect/mark_unpaid/$', MarkUnpaid.as_view(), name='stripe_connect_mark_unpaid'),
	url(r'^stripe_connect/mark_paid/$', MarkPaid.as_view(), name='stripe_connect_mark_paid'),
	url(r'^stripe_connect/charge/$', Charge.as_view(), name='stripe_connect_charge'),
	url(r'^stripe_connect/client_appointments/$', ClientAppointments.as_view(), name='stripe_connect_client_appointments'),

	url(r'^disable_stripe_connect/$', 'disable_stripe_connect', name='disable_stripe_connect'),
	url(r'^stripe_connect_success/$', 'stripe_connect_success', name='stripe_connect_success'),

	# url(r"^webhook/$", "webhook", name="payments_webhook"),

	# url(r"^a/subscribe/$", "subscribe", name="payments_ajax_subscribe"),
	# url(r"^a/change/plan/$", "change_plan", name="payments_ajax_change_plan"),
	# url(r"^a/cancel/$", "cancel", name="payments_ajax_cancel"),
	# url(
	#	 r"^subscribe/$",
	#	 login_required(SubscribeView.as_view()),
	#	 name="payments_subscribe"
	# ),
	# url(
	#	 r"^change/plan/$",
	#	 login_required(ChangePlanView.as_view()),
	#	 name="payments_change_plan"
	# ),
	# url(
	#	 r"^cancel/$",
	#	 login_required(CancelView.as_view()),
	#	 name="payments_cancel"
	# ),
)
