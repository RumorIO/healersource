# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HealerSettings'
        db.create_table(u'dashboard_healersettings', (
            ('key', self.gf('django.db.models.fields.SlugField')(max_length=50, primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=254, null=True, blank=True)),
        ))
        db.send_create_signal(u'dashboard', ['HealerSettings'])


    def backwards(self, orm):
        # Deleting model 'HealerSettings'
        db.delete_table(u'dashboard_healersettings')


    models = {
        u'dashboard.healersettings': {
            'Meta': {'object_name': 'HealerSettings'},
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['dashboard']