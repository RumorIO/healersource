from collections import defaultdict

from django.core.management.base import BaseCommand

from gratitude_stream.models import Report, SpammingUser


class Command(BaseCommand):

	help = 'Process spam reports.'

	def handle(self, *args, **options):
		"""Process spam reports and mark users who have comments or posts
		with at least MINIMUM_REPORTS_TO_BAN reports.
		Print usernames of users who have been flagged.
		"""

		MINIMUM_REPORTS_TO_BAN = 3

		# count reports
		posting_reports = defaultdict(int)
		for report in Report.objects.all():
			posting_reports[report.posting] += 1

		all_users_to_flag = {posting.user for posting, number_of_reports in posting_reports.iteritems()
			if number_of_reports >= MINIMUM_REPORTS_TO_BAN}

		#already_flagged_users = {su.user for su in SpammingUser.objects.all()}

		# flag users
		for user in all_users_to_flag:
			spamming_user, created = SpammingUser.objects.get_or_create(user=user)
			if created:
				print 'Flagged %s' % spamming_user
