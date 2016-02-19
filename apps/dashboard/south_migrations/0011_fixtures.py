# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


class Migration(DataMigration):
	def forwards(self, orm):
		"Write your forwards methods here."
		# Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
		orm['dashboard.healermails'].objects.create(
			slug='welcome_mail',
			title='Welcome email subject',
			body='mail\n{{ user }}\n{{ site|upper }}\n{{ template.title }}',
			body_html='',
			delay=3,
			once=False,
			process='welcome'
		)

	def backwards(self, orm):
		raise RuntimeError("Cannot reverse this migration.")

	models = {
		u'contenttypes.contenttype': {
			'Meta': {'ordering': "('name',)",
					 'unique_together': "(('app_label', 'model'),)",
					 'object_name': 'ContentType',
					 'db_table': "'django_content_type'"},
			'app_label': (
			'django.db.models.fields.CharField', [], {'max_length': '100'}),
			u'id': (
			'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'model': (
			'django.db.models.fields.CharField', [], {'max_length': '100'}),
			'name': (
			'django.db.models.fields.CharField', [], {'max_length': '100'})
		},
		u'dashboard.healeractions': {
			'Meta': {
			'unique_together': "(['action', 'content_type', 'object_pk'],)",
			'object_name': 'HealerActions'},
			'action': ('django.db.models.fields.CharField', [],
					   {'max_length': '254', 'db_index': 'True'}),
			'content_type': ('django.db.models.fields.related.ForeignKey', [],
							 {'to': u"orm['contenttypes.ContentType']"}),
			'created': ('django.db.models.fields.DateTimeField', [],
						{'auto_now_add': 'True', 'db_index': 'True',
						 'blank': 'True'}),
			u'id': (
			'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'object_pk': (
			'django.db.models.fields.PositiveIntegerField', [], {})
		},
		u'dashboard.healermails': {
			'Meta': {'object_name': 'HealerMails'},
			'body': ('django.db.models.fields.TextField', [], {}),
			'body_html': ('django.db.models.fields.TextField', [],
						  {'null': 'True', 'blank': 'True'}),
			'delay': ('django.db.models.fields.PositiveIntegerField', [], {}),
			u'id': (
			'django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'once': ('django.db.models.fields.BooleanField', [],
					 {'default': 'False', 'db_index': 'True'}),
			'process': ('django.db.models.fields.CharField', [],
						{'default': "'default'", 'max_length': '254',
						 'db_index': 'True'}),
			'slug': ('django.db.models.fields.SlugField', [],
					 {'unique': 'True', 'max_length': '50'}),
			'title': (
			'django.db.models.fields.CharField', [], {'max_length': '254'})
		},
		u'dashboard.healersettings': {
			'Meta': {'object_name': 'HealerSettings'},
			'description': (
			'django.db.models.fields.CharField', [], {'max_length': '254'}),
			'key': ('django.db.models.fields.SlugField', [],
					{'max_length': '50', 'primary_key': 'True'}),
			'type': ('django.db.models.fields.CharField', [],
					 {'max_length': '254', 'null': 'True', 'blank': 'True'}),
			'value': ('django.db.models.fields.TextField', [], {}),
			'web_only': ('django.db.models.fields.BooleanField', [],
						 {'default': 'True', 'db_index': 'True'})
		}
	}

	complete_apps = ['dashboard']
	symmetrical = True
