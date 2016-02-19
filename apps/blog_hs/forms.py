import HTMLParser
import urllib2
import feedparser
import re
import os
import traceback
from datetime import datetime
from time import mktime
from bs4 import BeautifulSoup

from django import forms
from django.conf import settings
from django.core.management import call_command
from django.core.mail import mail_admins
from django.forms import TextInput

from mezzanine.blog.models import BlogPost as Post
from mezzanine.core.models import CONTENT_STATUS_DRAFT, CONTENT_STATUS_PUBLISHED
from mezzanine.generic.models import Keyword, AssignedKeyword

from healers.utils import html_sanitize
from util.widgets import TinyEditor

from blog_hs.models import description_from_content
from blog_hs.management.commands.import_wordpress_hs import NotAllImportedExceptions
from blog_hs.utils import post_quality


def send_import_error(subject, **kwargs):
	message = []
	for key, value in kwargs.iteritems():
		message.append('{0}: {1}'.format(key, value))
	message.append(traceback.format_exc())
	mail_admins(subject, '\n'.join(message))


def get_latest_post_id(user):
	'''Return latest post id or None if user had no posts'''
	try:
		return Post.objects.filter(user=user).latest('pk').pk
	except Post.DoesNotExist:
		return

def set_status_to_draft(user, latest_post_id):
	posts = Post.objects.filter(user=user)
	if latest_post_id is not None:
		posts = posts.filter(pk__gt=latest_post_id)
	posts.update(status=1)


class BlogForm(forms.ModelForm):

#    slug = forms.SlugField(
#        max_length = 20,
#        help_text = _("a short version of the title consisting only of letters, numbers, underscores and hyphens."),
#    )

	status = forms.IntegerField(initial=2, widget=forms.HiddenInput())
	title = forms.CharField(label="Title", required=True, widget=forms.TextInput(attrs={'style': 'width: 470px; max-width: 98%;'}))
	content = forms.CharField(label="", required=False, widget=TinyEditor())

	class Meta:
		model = Post
		fields = [
			"status",
			"title",
			"content"
			]

	def __init__(self, user=None, *args, **kwargs):
		self.user = user
		super(BlogForm, self).__init__(*args, **kwargs)
		if self.instance.id:
			del self.fields['status']

	def clean_slug(self):
		if not self.instance.pk:
			if Post.objects.filter(user=self.user, publish_date__month=datetime.now().month, publish_date__year=datetime.now().year, slug=self.cleaned_data["slug"]).exists():
				raise forms.ValidationError(u"This field must be unique for username, year, and month")
			return self.cleaned_data["slug"]
		try:
			post = Post.objects.get(
				user=self.user,
				publish_date__month=self.instance.publish_date.month,
				publish_date__year=self.instance.publish_date.year,
				slug=self.cleaned_data["slug"]
			)
			if post != self.instance:
				raise forms.ValidationError(u"This field must be unique for username, year, and month")
		except Post.DoesNotExist:
			pass
		return self.cleaned_data["slug"]

	def clean_content(self):
		try:
			content = html_sanitize(self.cleaned_data['content'])
		except:
			content = html_sanitize(self.cleaned_data['content'].encode('utf-8'))

		return HTMLParser.HTMLParser().unescape(content.decode('utf-8', 'ignore'))

	def clean(self):
		if 'status' in self.cleaned_data:
			if self.cleaned_data['status'] == CONTENT_STATUS_PUBLISHED and not post_quality(self.cleaned_data['content']):
				raise forms.ValidationError(u"Your blog post must be at least 400 characters long to be published.")

	def save(self, commit=True):
		post = super(BlogForm, self).save(commit=False)
		post.gen_description = False
		post.content = self.cleaned_data['content']
		post.description = description_from_content(post)
		if commit:
			post.save()
		return post


class ImportRssForm(forms.Form):
	url = forms.CharField(label='Your Website', required=True, widget=TextInput(attrs={'size':'40'}))

	def detect_feeds(self, url):
		result = []

		if not url.startswith('http'):
			url = 'http://' + url
		try:
			response = urllib2.urlopen(url)
		except urllib2.URLError:
			return []
		html = BeautifulSoup(response.read())
		feed_urls = html.findAll("link", rel="alternate")
		for feed_link in feed_urls:
			feed_type = feed_link.get("type", None)
			if feed_type is None:
				continue
			if "rss" in feed_type or "atom" in feed_type:
				feed_url = feed_link.get("href", None)
				if feed_url:
					result.append(feed_url)
		if not feed_urls:
			feed_urls = html.findAll("a")
			for feed_link in feed_urls:
				feed_url = feed_link.get('href', None)
				if (feed_url and
					(feed_url.startswith(url) or 'http' not in feed_url) and
					('feed' in feed_url or 'rss' in feed_url
						or 'atom' in feed_url)):
					result.append(feed_url)
		return result

	def get_fulltext_url(self, url):
		return '%s?key=%s&max=10&url=%s' % (
			settings.FIVEFILTERS_URL,
			settings.FIVEFILTERS_KEY,
			re.sub(r'\w+://', '', url))

	def parse_rss(self, user, url):
		d = feedparser.parse(self.get_fulltext_url(url))
		if d['entries']:
			for entry in d['entries']:
				post = Post()
				post.title = entry.title
				post.user = user
				post.description = entry.summary
				date = None
				if hasattr(entry, 'published'):
					date = entry.published_parsed
				elif hasattr(entry, 'date'):
					date = entry.date_parsed
				if date:
					post.publish_date = datetime.fromtimestamp(mktime(date))
				post.status = CONTENT_STATUS_DRAFT
				if hasattr(entry, 'description'):
					post.content = entry.description
				else:
					post.content = post.tease
				post.save()
				for tag in getattr(entry, 'tags', []):
					tag = tag.get('term', '').strip()
					if tag:
						keyword = Keyword.objects.get_or_create(title=tag)[0]
						AssignedKeyword.objects.create(keyword=keyword, content_object=post)
			return True

	def mezzanine_parse_rss(self, user, url):
		latest_post_id = get_latest_post_id(user)
		try:
			call_command(
				'import_rss_hs',
				mezzanine_user=user.username,
				rss_url=self.get_fulltext_url(url))
			set_status_to_draft(user, latest_post_id)
			return True
		except (SystemExit, Exception):
			send_import_error(
				'Error rss import',
				username=user.username,
				rss_url=url)
			return False

	def save(self, request):
		error = False
		url = self.cleaned_data['url'].strip()
		if url:
			if url.startswith('feed://'):
				feeds_list = [url]
			else:
				feeds_list = self.detect_feeds(url)
				if not feeds_list:
					feeds_list = [url]
			for feed_url in feeds_list:
				if self.mezzanine_parse_rss(request.user, feed_url):
					return False
			error = True

		return error


class ImportWordpressForm(forms.Form):
	xml_file = forms.FileField(label='2. Select that file from your computer', required=True)

	def save(self, request):
		import_path = os.path.join(settings.PROJECT_ROOT, '..', 'import')
		if not os.path.exists(import_path):
			os.makedirs(import_path)

		now = datetime.now().strftime('%Y%m%d%H%M')
		file_name = '{0}_{1}_wordpress.xml'.format(request.user.username, now)
		file_path = os.path.join(import_path, file_name)
		with open(file_path, 'wb+') as destination:
			for chunk in self.cleaned_data['xml_file'].chunks():
				destination.write(chunk)

		latest_post_id = get_latest_post_id(request.user)
		try:
			call_command(
				'import_wordpress_hs',
				verbose=0,
				interactive=False,
				mezzanine_user=request.user.username,
				url=file_path)
			os.remove(file_path)
			set_status_to_draft(request.user, latest_post_id)
			return False
		except NotAllImportedExceptions as e:
			return e
		except (SystemExit, Exception):
			send_import_error(
				'Error wordpress import',
				username=request.user.username,
				filename=file_path)
			return True


class ImportBloggerForm(forms.Form):
	blog_url = forms.CharField(label='Blogger address (e.g. myblog.blogspot.com)', required=True, widget=TextInput(attrs={'size':'50'}))

	def save(self, request):
		latest_post_id = get_latest_post_id(request.user)
		try:
			call_command(
				'import_blogger_hs',
				mezzanine_user=request.user.username,
				page_url=self.cleaned_data['blog_url'])
			set_status_to_draft(request.user, latest_post_id)
			return False
		except (SystemExit, Exception):
			#Do not send error to admins
			#send_import_error(
			#	'Error blogger import',
			#	username=request.user.username,
			#	blog_id=self.cleaned_data['blog_url'])
			return True


class ImportTumblrForm(forms.Form):
	tumblr_user = forms.CharField(label='Tumblr username', required=True)

	def save(self, request):
		latest_post_id = get_latest_post_id(request.user)
		try:
			call_command(
				'import_tumblr_hs',
				mezzanine_user=request.user.username,
				tumblr_user=self.cleaned_data['tumblr_user'])
			set_status_to_draft(request.user, latest_post_id)
			return False
		except (SystemExit, Exception):
			send_import_error(
				'Error tumblr import',
				username=request.user.username,
				tumblr_user=self.cleaned_data['tumblr_user'])
			return True
