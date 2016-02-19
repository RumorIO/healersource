# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.utils import timezone

class Migration(DataMigration):

	def forwards(self, orm):
		"Write your forwards methods here."
		for item in orm['oauth_access.userassociation'].objects.all():
			ua = orm.UserAssociationDated.objects.create(
				user_assoc=item
			)
			ua.date_created = timezone.datetime(year=2010, month=8, day=15)
			ua.save()

		#raise RuntimeError("Cannot reverse this migration.")

	def backwards(self, orm):
		raise RuntimeError("Cannot reverse this migration.")

	models = {
		u'about.userassociationdated': {
			'Meta': {'object_name': 'UserAssociationDated'},
			'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'datetime.datetime.now', 'blank': 'True'}),
			'user_assoc': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['oauth_access.UserAssociation']", 'unique': 'True', 'primary_key': 'True'})
		},
		u'auth.group': {
			'Meta': {'object_name': 'Group'},
			u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
			'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
		},
		u'auth.permission': {
			'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
			'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
			u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
		},
		u'auth.user': {
			'Meta': {'object_name': 'User'},
			'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
			'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
			'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
			u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
			'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
			'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
			'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
			'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
			'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
			'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
		},
		u'contenttypes.contenttype': {
			'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
			'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
		},
		u'oauth_access.userassociation': {
			'Meta': {'unique_together': "[('user', 'service')]", 'object_name': 'UserAssociation'},
			'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
			u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
			'service': ('django.db.models.fields.CharField', [], {'max_length': '75', 'db_index': 'True'}),
			'token': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
			'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
		}
	}

	complete_apps = ['about']
	symmetrical = True
