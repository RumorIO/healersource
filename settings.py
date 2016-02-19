# -*- coding: utf-8 -*-
# Django settings for social pinax project.
from datetime import datetime

import os.path
import posixpath
import pinax
import sys

PINAX_ROOT = os.path.abspath(os.path.dirname(pinax.__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

# tells Pinax to use the default theme
PINAX_THEME = 'default'

try:
	from debug import DEBUG
except ImportError:
	DEBUG = False

INTERNAL_IPS = [
	'127.0.0.1',
]

ADMINS = [
	('Error', 'admin@healersource.com'),
]

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# https://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'US/Eastern'

# Language code for this installation. All choices can be found here:
# https://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "https://media.lawrence.com", "https://example.com/media/"
MEDIA_URL = "/site_media/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

# URL that handles the static files like app media.
# Example: "https://media.lawrence.com"
STATIC_URL = "/site_media/static/"

# Add or skip admin urls
ENABLE_ADMIN_URLS = False

DOWNTIME_MESSAGE = ""

TWILIO_ACCOUNT_SID = "AC8a06e95cb364887e4ca8911eb9a10689"
TWILIO_AUTH_TOKEN = "1c79584e7db2a20f126fc6a02850344f"
TWILIO_PHONE_NUMBER = "6463928075"

RUNNING_LOCAL = False

# Additional directories which hold static files
STATICFILES_DIRS = [
	os.path.join(PROJECT_ROOT, "media"),
	# os.path.join(PINAX_ROOT, "media", PINAX_THEME),
	]

STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	'compressor.finders.CompressorFinder',
	'dajaxice.finders.DajaxiceFinder',
)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "https://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

# Make this unique, and don't share it with anybody.
SECRET_KEY = "m^m-kg*xs#-#srb=o^&6e1vh&g5vq8yh7ou2gcg7o%7b=kl4f+"

MIDDLEWARE_CLASSES = [
	'util.middleware.ExceptionUserInfoMiddleware',
	'corsheaders.middleware.CorsMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'pinax.apps.account.middleware.LocaleMiddleware',
	'util.middleware.TrackingMiddleware',
]
# if not DEBUG:
# 	MIDDLEWARE_CLASSES += [
# 		'django.middleware.cache.UpdateCacheMiddleware',
# 		'django.middleware.common.CommonMiddleware',
# 		'django.middleware.cache.FetchFromCacheMiddleware',
# 	]
# else:
MIDDLEWARE_CLASSES += [
	'django.middleware.common.CommonMiddleware',
]
MIDDLEWARE_CLASSES += [
	'django.middleware.csrf.CsrfViewMiddleware',
	#'django_openid.consumer.SessionConsumer',
	'django.contrib.messages.middleware.MessageMiddleware',
	#'groups.middleware.GroupAwareMiddleware',
	'django.contrib.admindocs.middleware.XViewMiddleware',
	'pagination.middleware.PaginationMiddleware',
	'django_sorting.middleware.SortingMiddleware',
	'pinax.middleware.security.HideSensistiveFieldsMiddleware',

	'minidetector.Middleware',
	'about.middleware.DowntimeMiddleware',
	'util.middleware.BaseTemplateMiddleware'
]

# CACHE_MIDDLEWARE_SECONDS = 30
# CACHES = {
# 	'default': {
# 		'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
# 		'LOCATION': os.path.join(PROJECT_ROOT, 'cache'),
# 	}
# }
# CACHE_MIDDLEWARE_KEY_PREFIX = 'HealerSource'


ROOT_URLCONF = 'healersource.urls'

TEMPLATE_DIRS = [
	os.path.join(PROJECT_ROOT, "templates"),
	# os.path.join(PINAX_ROOT, "templates", PINAX_THEME),
	]

TEMPLATES = [
{
	'BACKEND': 'django.template.backends.django.DjangoTemplates',
	'DIRS': [os.path.join(PROJECT_ROOT, "templates")],
	# 'APP_DIRS': True,
	'OPTIONS': {
	'context_processors':
		(
			"django.contrib.auth.context_processors.auth",
			"django.core.context_processors.i18n",
			"django.core.context_processors.media",
			"django.core.context_processors.static",
			"django.core.context_processors.request",
			"django.contrib.messages.context_processors.messages",

			# "staticfiles.context_processors.static_url",

			"pinax.core.context_processors.pinax_settings",

			"pinax.apps.account.context_processors.account",

			#    "notification.context_processors.notification",
			#    "announcements.context_processors.site_wide_announcements",
			"django_messages.context_processors.inbox",
			#    "friends_app.context_processors.invitations",

			#    "healersource.context_processors.combined_inbox_count",

			"healers.context_processors.running_local_processor",
			"healers.context_processors.is_healer_processor",
			"healers.context_processors.unconfirmed_appointments_processor",
			"healers.context_processors.find_healer_processor",

			"healers.context_processors.client_invitations_processor",
			"sync_hs.context_processors.facebook_processor",
			#    "healers.context_processors.referral_invitations_processor"
			#	 "minidetector.context_processors.is_mob"

			#    "messages_hs.ajax.new_message_form_processor"
			"util.context_processors.impersonate",
		),
	'loaders': (
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
		'django.template.loaders.eggs.Loader',)
	}
},
]

# List of callables that know how to import templates from various sources.
if not DEBUG:
	TEMPLATE_LOADERS = (
		(
			'django.template.loaders.cached.Loader',
			(
				'django.template.loaders.filesystem.Loader',
				'django.template.loaders.app_directories.Loader',
				'django.template.loaders.eggs.Loader',
			)
		),
	)
else:
	TEMPLATE_LOADERS = (
		'django.template.loaders.filesystem.Loader',
		'django.template.loaders.app_directories.Loader',
		'django.template.loaders.eggs.Loader',)


TEMPLATE_CONTEXT_PROCESSORS = [
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	"django.core.context_processors.static",
	"django.core.context_processors.request",
	"django.contrib.messages.context_processors.messages",

	# "staticfiles.context_processors.static_url",

	"pinax.core.context_processors.pinax_settings",

	"pinax.apps.account.context_processors.account",

	#    "notification.context_processors.notification",
	#    "announcements.context_processors.site_wide_announcements",
	"django_messages.context_processors.inbox",
	#    "friends_app.context_processors.invitations",

	#    "healersource.context_processors.combined_inbox_count",

	"healers.context_processors.running_local_processor",
	"healers.context_processors.is_healer_processor",
	"healers.context_processors.unconfirmed_appointments_processor",
	"healers.context_processors.find_healer_processor",

	"healers.context_processors.client_invitations_processor",
	"sync_hs.context_processors.facebook_processor",
	#    "healers.context_processors.referral_invitations_processor"
	#	 "minidetector.context_processors.is_mob"

	#    "messages_hs.ajax.new_message_form_processor"
	"util.context_processors.impersonate",
]

COMBINED_INBOX_COUNT_SOURCES = [
	"django_messages.context_processors.inbox",
	#    "friends_app.context_processors.invitations",
	#    "notification.context_processors.notification",
]

INSTALLED_APPS = [
	# Django
	#    "django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.redirects",
	"django.contrib.sessions",
	"django.contrib.sites",
	"django.contrib.messages",
	"django.contrib.humanize",
	'markup_deprecated',
	"django_comments",
	"django.contrib.sitemaps",
	"django.contrib.gis",
	# 'django.contrib.admin',

	"pinax.templatetags",

	# external
	#    "notification", # must be first
	"django.contrib.staticfiles",
	"uni_form",
	# "django_openid",
	"ajax_validation",
	"timezones",
	"emailconfirmation",
	#    "announcements",
	"pagination",
	"friends",
	"django_messages",
	"oembed",
	#    "groups",
	#"threadedcomments",
	"wakawaka",
	#    "swaps",
	#    "voting",
	"tagging",
	#    "bookmarks",
	#    "photologue",
	"avatar",
	#    "flag",
	#    "microblogging",
	#    "locations",
	"django_sorting",
	"django_markup",
	"tagging_ext",
	"oauth_access",
	"captcha",

	# Pinax
	'pinax.apps.account',
	"pinax.apps.waitinglist",
	#    "pinax.apps.signup_codes",
	#    "pinax.apps.profiles",
	#"pinax.apps.blog",
	#    "pinax.apps.tribes",
	#    "pinax.apps.photos",
	#    "pinax.apps.topics",
	#"pinax.apps.threadedcomments_extras",
	#    "pinax.apps.voting_extras",

	# project
	"about",

	#healersource
	"dajaxice",
	"dajax",
	"clients",
	"healers",
	"schedule",
	"friends_hs",
	"friends_app",
	"feedback",
	"sync_hs",
	"modality",
	"contacts_hs",
	'client_notes',
	"blog_hs",
	"search",
	"mezzanine.conf",
	"mezzanine.core",
	"mezzanine.generic",
	"mezzanine.blog",
	"review",
	"errors_hs",
	"healing_requests",
	"audit",
	"send_healing",
	'metron',
	'account_hs',
	'compressor',
	"intake_forms",
	'django_select2',
	'payments',
	'util',
	'endless_pagination',
	'messages_hs',
	'dashboard',
	# 'django_extensions',
	'django_nose',
	'gratitude_stream',
	'provider',
	'provider.oauth2',
	'rest_framework',
	'corsheaders',
	'oauth2_hs',
	'events',
	'phonegap',
	'ambassador',
	'geonames'
]

# mezzanine settings
PACKAGE_NAME_FILEBROWSER = 'filebrowser_safe'
TESTING = False
GRAPPELLI_INSTALLED = False
PAGE_MENU_TEMPLATES = []
PAGE_MENU_TEMPLATES_DEFAULT = []
COMMENTS_DEFAULT_APPROVED = True
BLOG_URLS_DATE_FORMAT = 'month'
COMMENTS_UNAPPROVED_VISIBLE = True
COMMENTS_REMOVED_VISIBLE = False
COMMENTS_NOTIFICATION_EMAILS = ''
COMMENT_FILTER = None
RATINGS_ACCOUNT_REQUIRED = True
COMMENTS_ACCOUNT_REQUIRED = True
COMMENT_FORM_CLASS = 'mezzanine.generic.forms.ThreadedCommentForm'

COMPRESS_PARSER = 'compressor.parser.HtmlParser'

FIXTURE_DIRS = [
	os.path.join(PROJECT_ROOT, "fixtures"),
	]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ABSOLUTE_URL_OVERRIDES = {
	"auth.user": lambda o: "/profiles/profile/%s/" % o.username,
	}

MARKUP_FILTER_FALLBACK = "none"
MARKUP_CHOICES = [
	("restructuredtext", u"reStructuredText"),
	("textile", u"Textile"),
	("markdown", u"Markdown"),
	("creole", u"Creole"),
]

NOTIFICATION_LANGUAGE_MODULE = "account.Account"

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_REQUIRED_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_AUTHENTICATION = True
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = True
EMAIL_CONFIRMATION_DAYS = 7

DEFAULT_FROM_EMAIL = 'HealerSource (no reply) <no_reply@healersource.com>'
REPLY_TO = 'HealerSource (no reply) <no_reply@healersource.com>'
WELCOME_EMAIL_REPLY_TO = 'Daniel Levin <daniel@healersource.com>'

AUTHENTICATION_BACKENDS = [
	"account_hs.authentication.CaseInsensitiveAuthenticationBackend",
]

REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.OAuth2Authentication',
		'account_hs.authentication.RestSessionAuthentication',
	)
}

CAPTCHA_FONT_SIZE = 30

#LOGIN_URL = "/account/login/" # @@@ any way this can be a url name?
#LOGIN_REDIRECT_URLNAME = "what_next"

LOGIN_URL = "/login_redirect/"  # @@@ any way this can be a url name?
LOGIN_REDIRECT_URLNAME = "what_next"

ugettext = lambda s: s
LANGUAGES = [
	("en", u"English"),
]

# URCHIN_ID = "ua-..."

YAHOO_MAPS_API_KEY = "..."


class NullStream(object):
	def write(*args, **kwargs):
		pass
	writeline = write
	writelines = write

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
	"cloak_email_addresses": True,
	"file_insertion_enabled": False,
	"raw_enabled": False,
	"warning_stream": NullStream(),
	"strip_comments": True,
	}

# if Django is running behind a proxy, we need to do things like use
# HTTP_X_FORWARDED_FOR instead of REMOTE_ADDR. This setting is used
# to inform apps of this fact
BEHIND_PROXY = False

FORCE_LOWERCASE_TAGS = True

# Uncomment this line after signing up for a Yahoo Maps API key at the
# following URL: https://developer.yahoo.com/wsregapp/
# YAHOO_MAPS_API_KEY = ""

SITE_NAME = "HealerSource"
CONTACT_EMAIL = "admin@healersource.com"
SUPPORT_EMAIL = "support@healersource.com"

AVATAR_GRAVATAR_BACKUP = False

DAJAXICE_MEDIA_PREFIX = "dajaxice"

#GEOIP_PATH = os.path.join(PROJECT_ROOT, "geoip")

MAX_MODALITIES_PER_HEALER = 30
NUMBER_OF_MODALITIES_IN_AUTOCOMPLETE = 10

SOUTH_TESTS_MIGRATE = False
#POSTGIS_SQL_PATH = '/opt/local/share/postgresql83/contrib/postgis-1.5'
POSTGIS_TEMPLATE = 'template_postgis'

GET_NOW = datetime.utcnow

DKIM_SELECTOR = 'key1'
DKIM_DOMAIN = 'healersource.com'

FIVEFILTERS_URL = 'https://healersource.com/fivefilters/makefulltextfeed.php'

AUDIT_AVAILABILITY = True
AUDIT_APPOINTMENTS = True
MAILCHIMP_KEY = ''
MAILCHIMP_LIST_ID = ''
MAILCHIMP_IPHONE_LIST_ID = '60eacfbe89'

FACEBOOK_KEY = ''
FACEBOOK_SECRET = ''
STRIPE_SECRET_KEY = ''
GOOGLE_OAUTH_REDIRECT_URL = 'https://www.healersource.com/oauth2callback/google/'
GOOGLE_CLIENT_ID = ''
GOOGLE_CLIENT_SECRET = ''

MAX_GCAL_SYNC_RETRIES = 10
# Payments Settings Start

STRIPE_PUBLIC_KEY = ''
STRIPE_API_VERSION = '2012-11-07'
STRIPE_APP_CLIENT_ID = 'ca_4tGF2cdacsFNL5e5dKe3G9tcW8lQhd1s'

SCHEDULE_TRIAL_NUMBER_OF_DAYS = 30
SCHEDULE_USERS_WITH_FREE_ACCESS = []
STRIPE_CONNECT_BETA_USERS = []
GIFT_CERTIFICATES_BETA_USERS = []
NO_PROVIDER_STEP_USERS = []

NUMBER_OF_FREE_NOTES = 25

PAYMENTS_SCHEDULE_PAYMENT = 7
PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT = 49
PAYMENTS_NOTES_PAYMENT = 15

BOOKING_HEALERSOURCE_FEE = 15


def get_payment_plans(amounts=None):
	def get_payment_plans_list(schedule=False, notes=False):
		def add_additional_schedule_plans(plans):
			providers_in_center = 1
			while True:
				providers_in_center += 1
				for amount in range_list:
					total_amount = amount * providers_in_center
					if total_amount > PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT:
						return plans
					plans.add(total_amount)
			return plans

		if schedule:
			payment = PAYMENTS_SCHEDULE_PAYMENT
		if notes:
			payment = PAYMENTS_NOTES_PAYMENT

		range_list = [payment]
		plans = set(range_list)
		if schedule:
			plans = add_additional_schedule_plans(plans)
			plans |= set(CUSTOM_SCHEDULE_PAYMENT_AMOUNTS)
			plans.add(PAYMENTS_SCHEDULE_UNLIMITED_PAYMENT)
		return list(plans)

	def add_plans(name, amounts):
		title = name.capitalize()
		for n in amounts:
			plan_id = '%s_%d' % (name, n)
			payment_plans[plan_id] = {
				'stripe_plan_id': plan_id,
				'name': '%s ($%d/month)' % (title, n),
				'description': 'The monthly subscription plan to Healersource %s' % title,
				'price': n,
				'currency': 'usd',
				'interval': 'month'}

	if amounts is None:
		amounts_schedule = get_payment_plans_list(schedule=True)
		amounts_notes = get_payment_plans_list(notes=True)
	else:
		amounts_schedule = amounts_notes = amounts

	payment_plans = {}
	add_plans('schedule', amounts_schedule)
	add_plans('notes', amounts_notes)
	add_plans('booking', [BOOKING_HEALERSOURCE_FEE])

	return payment_plans

PLAN_TYPES = ['schedule', 'notes', 'booking']
TEST_PAYMENTS_PLANS = get_payment_plans([15, 30, 45])
CUSTOM_SCHEDULE_PAYMENT_AMOUNTS = [50, 100, 200]

TEST_INIT_PLANS = True
TEST_REMOVE_CUSTOMERS = True


# Payments Settings End

SH_NUMBER_OF_LOCATIONS_ON_MAP = 111
SH_MIN_DURATION = 2

NOTES_DEFAULT_FAVORITE_DIAGRAMS = [1, 2]

CORS_ORIGIN_ALLOW_ALL = True

PHONEGAP_VERSION = [1, 0]
PHONEGAP_VERSION2 = [1, 0]
PHONEGAP_VERSION_FILE_PATH = os.path.join(PROJECT_ROOT, 'phonegap.version')
PHONEGAP_VERSION2_FILE_PATH = os.path.join(PROJECT_ROOT, 'phonegap2.version')
PHONEGAP_LIST_VERSION = 1

STRIPE_CONNECT_PAYMENTS_NUMBER_OF_DAYS = 30
MAX_PROVIDERS_ON_SPECIALITY_PAGE = 7

FILE_UPLOAD_PERMISSIONS = 0664

TRACKING_CODES = {
	'client': {'fb': '6016753467688'},
	'healer': {'fb': '6014369859534'},
	'wellness_center': {'fb': '6014369859534'},  # 6016753473888

	'notes_landing': {'fb': '6022224313334', 'google': '979565045',
		'optimizely': {'experiment_id': '2425320641', 'event_name': 'soap_signup'}},
	'book_landing': {'fb': '', 'google': ''}
}

UTM_TRACKING_PARAMETERS = ['utm_source', 'utm_medium', 'utm_term', 'utm_campaign', 'utm_content']

USERNAME_MIN_LENGTH = 6
USERNAME_MAX_LENGTH = 30

DEFAULT_HTTP_PROTOCOL = 'https'

DATABASE_ROUTERS = ['geonames.db_routers.GeoNamesRouter']

# Logging
from django.core.exceptions import ObjectDoesNotExist


def skip_doesnotexist(record):
	if record.exc_info:
		exc_type, exc_value = record.exc_info[:2]
		if isinstance(exc_value, ObjectDoesNotExist):
			return False
	return True

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'filters': {
		'require_debug_false': {
			'()': 'django.utils.log.RequireDebugFalse',
		},
		'require_debug_true': {
			'()': 'django.utils.log.RequireDebugTrue',
		},
		'skip_doesnotexist': {
			'()': 'django.utils.log.CallbackFilter',
			'callback': skip_doesnotexist,
		}
	},
	'handlers': {
		'console': {
			'level': 'INFO',
			'filters': ['require_debug_true'],
			'class': 'logging.StreamHandler',
		},
		'null': {
			'class': 'logging.NullHandler',
		},
		'mail_admins': {
			'level': 'ERROR',
			'filters': ['require_debug_false', 'skip_doesnotexist'],
			'class': 'django.utils.log.AdminEmailHandler'
		}
	},
	'loggers': {
		'django': {
			'handlers': ['console'],
		},
		'django.request': {
			'handlers': ['mail_admins'],
			'level': 'ERROR',
			'propagate': False,
		},
		'django.security': {
			'handlers': ['mail_admins'],
			'level': 'ERROR',
			'propagate': False,
		},
		'py.warnings': {
			'handlers': ['console'],
		},
	}
}

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
try:
	from local_settings import *
except ImportError:
	pass

PAYMENTS_PLANS = get_payment_plans()

OAUTH_ACCESS_SETTINGS = {
	'google': {
		'scope': [
			'https://www.googleapis.com/auth/calendar',
			'https://www.googleapis.com/auth/userinfo.email',  # get email
			'https://www.google.com/m8/feeds',  # contacts write access
			# 'https://www.googleapis.com/auth/contacts.readonly',
		],
		'redirect_uri': GOOGLE_OAUTH_REDIRECT_URL,
		'client_id': GOOGLE_CLIENT_ID,
		'client_secret': GOOGLE_CLIENT_SECRET,
		'access_type': 'offline',
		'approval_prompt': 'force',
	},
	'facebook': {
			'keys': {'KEY': FACEBOOK_KEY, 'SECRET': FACEBOOK_SECRET},
			'endpoints': {
				'request_token': 'https://graph.facebook.com/oauth/request_token',
				'access_token': 'https://graph.facebook.com/oauth/access_token',
				'authorize': 'https://graph.facebook.com/oauth/authorize',
				'callback': 'sync_hs.facebook.facebook_callback',
				'provider_scope': ['user_website', 'email', 'user_friends',
									'user_location', 'user_photos'],
				'scopes_to_check': ['user_friends']
			}
	},
	'stripe': {
			'keys': {'KEY': '', 'SECRET': STRIPE_SECRET_KEY},
			'endpoints': {
				'request_token': 'https://connect.stripe.com/oauth/token',
				'access_token': 'https://connect.stripe.com/oauth/token',
				'authorize': 'https://connect.stripe.com/oauth/authorize',
				'callback': 'payments.stripe_connect.stripe_callback',
				'provider_scope': ['read_write'],
				'scopes_to_check': ['read_write']
			}
	}
}

STRIPE_CONNECT_LINK = '{}?response_type=code&client_id={}&scope={}'.format(OAUTH_ACCESS_SETTINGS['stripe']['endpoints']['authorize'],
	STRIPE_APP_CLIENT_ID, OAUTH_ACCESS_SETTINGS['stripe']['endpoints']['provider_scope'][0])

# tells Pinax to serve media through the staticfiles app.
SERVE_MEDIA = DEBUG
EMAIL_DEBUG = DEBUG
TEMPLATE_DEBUG = DEBUG

if not DEBUG:
	INSTALLED_APPS.append("django_yubin")

INVITATION_BACKGROUND_ROOT = os.path.join(MEDIA_ROOT, 'invitation_backgrounds')
INVITATION_BACKGROUND_URL = MEDIA_URL + 'invitation_backgrounds/'
DEFAULT_INVITATION_BACKGROUND = 'Ghandiji.jpg'

LANDING_NOTES_ROOT = os.path.join(MEDIA_ROOT, 'landing_notes')

FEATURED_PROVIDERS_ROOT = os.path.join(MEDIA_ROOT, 'featured')
FEATURED_PROVIDERS_URL = MEDIA_URL + 'featured/'

MODALITY_MENU_PATH = os.path.join(MEDIA_ROOT, 'modality_list.html')

AVATAR_DEFAULT_URL = 'healersource/img/hs_avatar.png'
AVATAR_CLEANUP_DELETED = True
AVATAR_AUTO_GENERATE_SIZES = (32, 40, 50, 60, 90, 94, 100, 130, 140, 148)
AVATAR_MAX_WIDTH = 320
AVATAR_MAX_HEIGHT = 320

DEFAULT_MODALITY_TEXT = 'Healer'
DEFAULT_LOCATION_TEXT = 'USA'

ALLOWED_IMAGE_UPLOAD_TYPES = ['jpeg', 'jpg', 'png', 'gif']

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
