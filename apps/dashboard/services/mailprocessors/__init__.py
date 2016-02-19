MAIL_PROCESSOR_DEFAULT = 'default'
MAIL_PROCESSOR_WELCOME = 'welcome'
MAIL_PROCESSOR_SEND_ON_REQUEST = 'send_on_request'
MAIL_PROCESSOR_GHP = 'ghp'


MAIL_PROCESSORS = (
	(MAIL_PROCESSOR_DEFAULT, 'Default processor'),
	(MAIL_PROCESSOR_WELCOME, 'Welcome mail processor'),
	(MAIL_PROCESSOR_SEND_ON_REQUEST, 'Send on request processor'),
	(MAIL_PROCESSOR_GHP, 'Global Healing Project processor')
)
