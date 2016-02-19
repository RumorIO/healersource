# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'HealerSettings.description'
        db.add_column(u'dashboard_healersettings', 'description',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=254),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'HealerSettings.description'
        db.delete_column(u'dashboard_healersettings', 'description')


    models = {
        u'dashboard.healersettings': {
            'Meta': {'object_name': 'HealerSettings'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['dashboard']