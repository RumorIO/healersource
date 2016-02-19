# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Renaming column for 'HealerTimeslotAudit.timeslot' to match new field type.
        db.rename_column('audit_healertimeslotaudit', 'timeslot_id', 'timeslot')
        # Changing field 'HealerTimeslotAudit.timeslot'
        db.alter_column('audit_healertimeslotaudit', 'timeslot', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Removing index on 'HealerTimeslotAudit', fields ['timeslot']
        db.delete_index('audit_healertimeslotaudit', ['timeslot_id'])

        # Renaming column for 'AppointmentAudit.timeslot' to match new field type.
        db.rename_column('audit_appointmentaudit', 'timeslot_id', 'timeslot')
        # Changing field 'AppointmentAudit.timeslot'
        db.alter_column('audit_appointmentaudit', 'timeslot', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Removing index on 'AppointmentAudit', fields ['timeslot']
        db.delete_index('audit_appointmentaudit', ['timeslot_id'])


    def backwards(self, orm):
        
        # Adding index on 'AppointmentAudit', fields ['timeslot']
        db.create_index('audit_appointmentaudit', ['timeslot_id'])

        # Adding index on 'HealerTimeslotAudit', fields ['timeslot']
        db.create_index('audit_healertimeslotaudit', ['timeslot_id'])

        # Renaming column for 'HealerTimeslotAudit.timeslot' to match new field type.
        db.rename_column('audit_healertimeslotaudit', 'timeslot', 'timeslot_id')
        # Changing field 'HealerTimeslotAudit.timeslot'
        db.alter_column('audit_healertimeslotaudit', 'timeslot_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['healers.HealerTimeslot']))

        # Renaming column for 'AppointmentAudit.timeslot' to match new field type.
        db.rename_column('audit_appointmentaudit', 'timeslot', 'timeslot_id')
        # Changing field 'AppointmentAudit.timeslot'
        db.alter_column('audit_appointmentaudit', 'timeslot_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['healers.Appointment']))


    models = {
        'audit.appointmentaudit': {
            'Meta': {'object_name': 'AppointmentAudit'},
            'after': ('django.db.models.fields.TextField', [], {}),
            'before': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timeslot': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'audit.healertimeslotaudit': {
            'Meta': {'object_name': 'HealerTimeslotAudit'},
            'after': ('django.db.models.fields.TextField', [], {}),
            'before': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timeslot': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 8, 13, 7, 37, 21, 859174)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 8, 13, 7, 37, 21, 858973)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['audit']
