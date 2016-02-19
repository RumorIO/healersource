# coding=utf-8
from dashboard.services.mailprocessors.default import \
	MailProcessor as DefaultProcessor


PROCESSOR = ('send_on_request', 'Send on request processor')


class MailProcessor(DefaultProcessor):
	pass
