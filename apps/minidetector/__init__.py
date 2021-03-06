from datetime import datetime
from django.conf import settings

from django import http
from minidetector.useragents import search_strings
#import os.path

class Middleware(object):
	@staticmethod
	def process_request(request):
		""" Adds a "mobile" attribute to the request which is True or False
						depending on whether the request should be considered to come from a
						small-screen device such as a phone or a PDA"""

		request.is_mobile = False
		request.is_iphone = False

		if request.META.has_key("HTTP_X_OPERAMINI_FEATURES"):
			#Then it's running opera mini. 'Nuff said.
			#Reference from:
			# http://dev.opera.com/articles/view/opera-mini-request-headers/

			request.is_simple_device = True

			request.is_mobile = True

		if request.META.has_key("HTTP_ACCEPT"):
			s = request.META["HTTP_ACCEPT"].lower()
			if 'application/vnd.wap.xhtml+xml' in s:
				# Then it's a wap browser

				request.is_simple_device = True

				request.is_mobile = True

		if request.META.has_key("HTTP_USER_AGENT"):
			# This takes the most processing. Surprisingly enough, when I
			# Experimented on my own machine, this was the most efficient
			# algorithm. Certainly more so than regexes.
			# Also, Caching didn't help much, with real-world caches.

			s = request.META["HTTP_USER_AGENT"].lower()

			if 'applewebkit' in s:
				request.is_webkit = True

			if 'ipad' in s:
				request.is_ios_device = True
				request.is_touch_device = True
				request.is_wide_device = True

				request.is_mobile = True

			if 'iphone' in s or 'ipod' in s:
				request.is_ios_device = True
				request.is_touch_device = True
				request.is_wide_device = False
				request.is_iphone = True

				request.is_mobile = True

			if 'android' in s:
				request.is_android_device = True
				request.is_touch_device = True
				request.is_wide_device = False # TODO add support for andriod tablets

				request.is_mobile = True

			if 'webos' in s:
				request.is_webos_device = True
				request.is_touch_device = True
				request.is_wide_device = False # TODO add support for webOS tablets

				request.is_mobile = True

			if 'windows phone' in s:
				request.is_windows_phone_device = True
				request.is_touch_device = True
				request.is_wide_device = False

				request.is_mobile = True

			for ua in search_strings:
				if ua in s:
					request.is_simple_device = True
					request.is_mobile = True

		#request.base_template = "base.html"

		if not request.is_mobile:
			request.is_simple_device = False
			request.is_touch_device = False
			request.is_wide_device = True

		return None


def detect_mobile(view):
	""" View Decorator that adds a "mobile" attribute to the request which is
			  True or False depending on whether the request should be considered
			  to come from a small-screen device such as a phone or a PDA"""

	def detected(request, *args, **kwargs):
		Middleware.process_request(request)
		return view(request, *args, **kwargs)
	detected.__doc__ = "%s\n[Wrapped by detect_mobile which detects if the request is from a phone]" % view.__doc__
	return detected

__all__ = ['Middleware', 'detect_mobile']