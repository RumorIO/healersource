from datetime import datetime, timedelta
from time import timezone
from urllib import urlopen
from urlparse import urljoin

from django.core.management.base import CommandError

from blog_hs.models import description_from_content
from mezzanine.blog.management.commands.import_blogger\
	import Command as BloggerCommand

from healers.utils import html_sanitize


class Command(BloggerCommand):
	"""
	Extends import_blogger command to override post description
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

		rss_url = options.get("rss_url")
		page_url = options.get("page_url")
		if page_url and not page_url.startswith('http://'):
			page_url = 'http://' + page_url
		if not (page_url or rss_url):
			raise CommandError("Either --rss-url or --page-url option "
							   "must be specified")

		try:
			from dateutil import parser
		except ImportError:
			raise CommandError("dateutil package is required")
		try:
			from feedparser import parse
		except ImportError:
			raise CommandError("feedparser package is required")
		if not rss_url and page_url:
			try:
				from bs4 import BeautifulSoup
			except ImportError:
				raise CommandError("BeautifulSoup package is required")
			try:
				for l in BeautifulSoup(urlopen(page_url).read()).findAll("link"):
					if ("application/rss" in l.get("type", "") or
						"application/atom" in l.get("type", "")):
						rss_url = urljoin(page_url, l["href"])
						break
				else:
					raise CommandError("Could not parse RSS link from the page")
			except :
				raise CommandError("Could not parse RSS link from the page")

		posts = parse(rss_url)["entries"]
		for post in posts:
			if hasattr(post, 'content'):
				content = post.content[0]["value"]
			else:
				content = post.summary
			tags = [tag["term"] for tag in getattr(post, 'tags', [])]
			try:
				pub_date = parser.parse(post.updated)
			except AttributeError:
				pub_date = datetime.now()
			self.add_post(title=post.title, content=html_sanitize(content),
						  pub_date=pub_date, tags=tags)
