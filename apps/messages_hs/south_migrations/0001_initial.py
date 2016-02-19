# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnregisteredMessage'
        db.create_table(u'messages_hs_unregisteredmessage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'messages_hs', ['UnregisteredMessage'])


    def backwards(self, orm):
        # Deleting model 'UnregisteredMessage'
        db.delete_table(u'messages_hs_unregisteredmessage')


    models = {
        u'messages_hs.unregisteredmessage': {
            'Meta': {'object_name': 'UnregisteredMessage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['messages_hs']