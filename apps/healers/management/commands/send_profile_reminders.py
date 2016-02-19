from datetime import timedelta, date
from optparse import make_option
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from healers.models import Healer, is_wellness_center
from healers.utils import send_hs_mail, get_full_url, get_fill_warning_links


class Command(BaseCommand):

	help = 'Send an email reminder to each provider that does not pass all 3 profile completeness requirements'

	option_list = BaseCommand.option_list + (
		make_option('--username',
			action='store',
			dest='username',
			default=None,
			help='only send reminders for username'),
	)

	def handle(self, *args, **options):
		def get_providers_with_no_location():
			providers = healers.filter(remote_sessions=False)
			providers_with_no_location = []
			for provider in providers:
				if not provider.get_locations():
					providers_with_no_location.append(provider)
			return providers_with_no_location

		healers = Healer.objects.filter(is_deleted=False, user__is_active=True)

		providers_blank = healers.filter(Q(user__avatar__isnull=True) | Q(about='')).distinct()

		providers_no_modality = healers.annotate(modality_count=Count('modality')).filter(modality_count=0)
		# filter wellness centers because of specialities of their providers
		providers_no_modality = (
			provider
			for provider in providers_no_modality
			if not is_wellness_center(provider) or not provider.has_specialities())

		providers = set(list(providers_blank) + list(providers_no_modality) + get_providers_with_no_location())

		username = options['username']
		for provider in providers:
			if username and provider.user.username != username:
				continue

			lastdate = provider.profile_completeness_reminder_lastdate
			interval = provider.profile_completeness_reminder_interval
			if username or not lastdate or lastdate + timedelta(weeks=interval) <= date.today():
				site_base = unicode(Site.objects.get_current())
				ctx = {
					'first_name': provider.user.first_name,
					'reminder_interval_link': get_full_url('healer_edit'),
					'change_reminder_interval_url': get_full_url('healer_change_profile_reminder_interval'),
					'change_reminder_interval_options': Healer.PROFILE_REMINDER_INTERVAL_CHOICES,
					'fill_warning_links': get_fill_warning_links(provider),
					'site_base': site_base
				}
				subject = render_to_string("healers/emails/profile_reminder_subject.txt", ctx)
				send_hs_mail(subject,
					'healers/emails/profile_reminder_message.txt',
					ctx,
					settings.DEFAULT_FROM_EMAIL,
					[provider.user.email])
				provider.profile_completeness_reminder_lastdate = date.today()
				provider.save()
