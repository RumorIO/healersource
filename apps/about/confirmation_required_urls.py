from django.conf.urls import patterns, url

from about.views import EmailConfirmationRequiredView


urlpatterns = patterns('',
	url(r"^schedule/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Schedule'}, name='feature_schedule'),
	url(r"^payments/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Payments'}, name='feature_payments'),
	url(r"^blog/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Blog'}, name='feature_blog'),
	url(r"^reviews/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Reviews'}, name='feature_reviews'),
	url(r"^intake/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Intake'}, name='feature_intake'),
	url(r"^notes/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Notes'}, name='feature_notes'),
	url(r"^inbox/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Inbox'}, name='feature_inbox'),
	url(r"^providers/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Providers'}, name='feature_providers'),
	url(r"^referrals/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Referrals'}, name='feature_referrals'),
	url(r"^clients/$",
		EmailConfirmationRequiredView.as_view(), kwargs={'feature': 'Clients'}, name='feature_clients'),
)
