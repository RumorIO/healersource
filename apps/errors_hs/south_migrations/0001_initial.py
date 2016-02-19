# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ErrorReport'
        db.create_table('errors_hs_errorreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 4, 16, 8, 19, 7, 696383))),
            ('report', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('errors_hs', ['ErrorReport'])


    def backwards(self, orm):
        
        # Deleting model 'ErrorReport'
        db.delete_table('errors_hs_errorreport')


    models = {
        'errors_hs.errorreport': {
            'Meta': {'object_name': 'ErrorReport'},
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 4, 16, 8, 19, 7, 696383)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['errors_hs']
