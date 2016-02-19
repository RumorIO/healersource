from collections import defaultdict
from datetime import datetime, timedelta
from time import mktime, timezone
from xml.dom.minidom import parse

from django.core.management.base import CommandError
from django.utils.html import linebreaks

from blog_hs.models import description_from_content
from mezzanine.blog.management.commands.import_wordpress\
	import Command as WordPressCommand

from healers.utils import html_sanitize

class NotAllImportedExceptions(Exception):
	"""
	If import done but with errors
	"""
	pass


class Command(WordPressCommand):
	"""
	Extends import_wordpress command to skip pages, skip bad posts
	and override post description generation
	"""

	def __init__(self, **kwargs):
		self.errors = False
		super(Command, self).__init__(**kwargs)

	def handle(self, *args, **options):
		"""
		Processes the converted data into the Mezzanine database correctly.

		Attributes:
			mezzanine_user: the user to put this data in against
			date_format: the format the dates are in for posts and comments
		"""

		super(Command, self).handle(*args, **options)
		if self.errors:
			raise NotAllImportedExceptions(
				"We had some trouble importing one or more of your posts. "
				"Sorry for the inconvenience!")

	def handle_import(self, options):
		"""
		Gets the posts from either the provided URL or the path if it
		is local.
		"""

		url = options.get("url")
		if url is None:
			raise CommandError("Usage is import_wordpress %s" % self.args)
		try:
			import feedparser
		except ImportError:
			raise CommandError("Could not import the feedparser library.")
		try:
			from bs4 import BeautifulSoup
		except ImportError:
			raise CommandError("BeautifulSoup package is required")
		feed = feedparser.parse(url)

		# We use the minidom parser as well because feedparser won't
		# interpret WXR comments correctly and ends up munging them.
		# xml.dom.minidom is used simply to pull the comments when we
		# get to them.
		xml = parse(url)
		xmlitems = xml.getElementsByTagName("item")

		for (i, entry) in enumerate(feed["entries"]):
			try:
				# Get a pointer to the right position in the minidom as well.
				xmlitem = xmlitems[i]
				content = linebreaks(self.wp_caption(entry.content[0]["value"]))

				# Get the time struct of the published date if possible and
				# the updated date if we can't.
				pub_date = getattr(entry,
								   "published_parsed",
								   entry.updated_parsed)
				pub_date = datetime.fromtimestamp(mktime(pub_date))
				pub_date -= timedelta(seconds=timezone)

				# Tags and categories are all under "tags" marked with a scheme.
				terms = defaultdict(set)
				for item in getattr(entry, "tags", []):
					terms[item.scheme].add(item.term)
				if entry.wp_post_type == "post":
					post = self.add_post(title=entry.title, content=html_sanitize(content),
										 pub_date=pub_date, tags=terms["tag"],
										 categories=terms["category"],
										 old_url=entry.id)

					# Get the comments from the xml doc.
					for c in xmlitem.getElementsByTagName("wp:comment"):
						name = self.get_text(c, "author", c.CDATA_SECTION_NODE)
						email = self.get_text(c, "author_email", c.TEXT_NODE)
						url = self.get_text(c, "author_url", c.TEXT_NODE)
						body = self.get_text(c, "content", c.CDATA_SECTION_NODE)
						pub_date = self.get_text(c, "date_gmt", c.TEXT_NODE)
						fmt = "%Y-%m-%d %H:%M:%S"
						pub_date = datetime.strptime(pub_date, fmt)
						pub_date -= timedelta(seconds=timezone)
						self.add_comment(post=post, name=name, email=email,
										 body=body, website=url,
										 pub_date=pub_date)

			except Exception:
				self.errors = True

	def add_meta(self, post, *args, **kwargs):
		"""
		Replace description after meta updating
		"""
		super(Command, self).add_meta(post, *args, **kwargs)
		post.gen_description = False
		post.description = description_from_content(post)
		post.save()
