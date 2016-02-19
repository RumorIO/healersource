# -*- coding: utf-8 -*-
import datetime
from mezzanine.blog.models import BlogPost
from mezzanine.core.models import CONTENT_STATUS_DRAFT
from south.db import db
from south.v2 import DataMigration
from django.db import models
from blog_hs.utils import post_quality


class Migration(DataMigration):
	def forwards(self, orm):
		blog_posts = BlogPost.objects.all()
		for blog_post in blog_posts:
			if not post_quality(blog_post.content):
				blog_post.status = CONTENT_STATUS_DRAFT
				blog_post.save()

	def backwards(self, orm):
		pass

	models = {}

	complete_apps = ['blog_hs']
	symmetrical = True
