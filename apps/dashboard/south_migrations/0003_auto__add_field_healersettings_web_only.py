# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'HealerSettings.web_only'
        db.add_column(u'dashboard_healersettings', 'web_only',
                      self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'HealerSettings.web_only'
        db.delete_column(u'dashboard_healersettings', 'web_only')


    models = {
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