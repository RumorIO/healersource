import json
from time import sleep
from urllib import urlopen
from datetime import datetime

from django.core.management.base import CommandError

from blog_hs.models import description_from_content
from mezzanine.blog.management.commands.import_tumblr import (
	Command as BloggerCommand, MAX_RETRIES_PER_CALL, MAX_POSTS_PER_CALL)
from healers.utils import html_sanitize


class Command(BloggerCommand):
	"""
	Extends import_tumblr command to override post description
	"""

	def add_meta(self, post, *args, **kwargs):
		"""
		Replace description after meta updating
		"""
		super(Command, self).add_meta(post, *args, **kwargs)
		post.gen_description = False
		post.description = description_from_content(post)
		post.save()

	def handle_import(self, options):

		tumblr_user = options.get("tumblr_user")
		if tumblr_user is None:
			raise CommandError("Usage is import_tumblr %s" % self.args)
		verbosity = int(options.get("verbosity", 1))
		json_url = "http://%s.tumblr.com/api/read/json" % tumblr_user
		json_start = "var tumblr_api_read ="
		date_format = "%a, %d %b %Y %H:%M:%S"
		start_index = 0

		while True:
			retries = MAX_RETRIES_PER_CALL
			try:
				call_url = "%s?start=%s" % (json_url, start_index)
				if verbosity >= 2:
					print "Calling %s" % call_url
				response = urlopen(call_url)
				if response.code == 404:
					raise CommandError("Invalid Tumblr user.")
				elif response.code == 503:
					# The Tumblr API is frequently unavailable so make a
					# few tries, pausing between each.
					retries -= 1
					if not retries:
						error = "Tumblr API unavailable, try again shortly."
						raise CommandError(error)
					sleep(3)
					continue
				elif response.code != 200:
					raise IOError("HTTP status %s" % response.code)
			except IOError, e:
				error = "Error communicating with Tumblr API (%s)" % e
				raise CommandError(error)

			data = response.read()
			posts = json.loads(
				data.split(json_start, 1)[1].strip().rstrip(";"))["posts"]
			start_index += MAX_POSTS_PER_CALL

			for post in posts:
				handler = getattr(self, "handle_%s_post" % post["type"])
				if handler is not None:
					title, content = handler(post)
					pub_date = datetime.strptime(post["date"], date_format)
					self.add_post(title=title, content=html_sanitize(content),
								  pub_date=pub_date, tags=post.get("tags"),
								  old_url=post["url-with-slug"])
			if len(posts) < MAX_POSTS_PER_CALL:
				break
