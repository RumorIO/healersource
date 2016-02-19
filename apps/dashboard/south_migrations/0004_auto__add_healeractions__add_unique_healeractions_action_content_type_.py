# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HealerActions'
        db.create_table(u'dashboard_healeractions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=254, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_pk', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'dashboard', ['HealerActions'])

        # Adding unique constraint on 'HealerActions', fields ['action', 'content_type', 'object_pk']
        db.create_unique(u'dashboard_healeractions', ['action', 'content_type_id', 'object_pk'])


    def backwards(self, orm):
        # Removing unique constraint on 'HealerActions', fields ['action', 'content_type', 'object_pk']
        db.delete_unique(u'dashboard_healeractions', ['action', 'content_type_id', 'object_pk'])

        # Deleting model 'HealerActions'
        db.delete_table(u'dashboard_healeractions')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dashboard.healeractions': {
            'Meta': {'unique_together': "(['action', 'content_type', 'object_pk'],)", 'object_name': 'HealerActions'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_pk': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'dashboard.healersettings': {
            'Meta': {'object_name': 'HealerSettings'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {}),
            'web_only': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['dashboard']