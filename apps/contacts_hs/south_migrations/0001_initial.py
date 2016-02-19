# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ContactInfo'
        db.create_table('contacts_hs_contactinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['friends.Contact'], null=True, blank=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['clients.Client'], null=True, blank=True)),
            ('healer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='healer_contacts', to=orm['healers.Healer'])),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal('contacts_hs', ['ContactInfo'])

        # Adding model 'ContactGroup'
        db.create_table('contacts_hs_contactgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('contacts_hs', ['ContactGroup'])

        # Adding M2M table for field contacts on 'ContactGroup'
        db.create_table('contacts_hs_contactgroup_contacts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('contactgroup', models.ForeignKey(orm['contacts_hs.contactgroup'], null=False)),
            ('contactinfo', models.ForeignKey(orm['contacts_hs.contactinfo'], null=False))
        ))
        db.create_unique('contacts_hs_contactgroup_contacts', ['contactgroup_id', 'contactinfo_id'])

        # Adding model 'ContactPhones'
        db.create_table('contacts_hs_contactphones', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(related_name='phone_numbers', to=orm['contacts_hs.ContactInfo'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='Mobile', max_length=42)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=42)),
        ))
        db.send_create_signal('contacts_hs', ['ContactPhones'])

        # Adding model 'ContactEmail'
        db.create_table('contacts_hs_contactemail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(related_name='emails', to=orm['contacts_hs.ContactInfo'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='Other', max_length=42)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=42)),
        ))
        db.send_create_signal('contacts_hs', ['ContactEmail'])


    def backwards(self, orm):
        
        # Deleting model 'ContactInfo'
        db.delete_table('contacts_hs_contactinfo')

        # Deleting model 'ContactGroup'
        db.delete_table('contacts_hs_contactgroup')

        # Removing M2M table for field contacts on 'ContactGroup'
        db.delete_table('contacts_hs_contactgroup_contacts')

        # Deleting model 'ContactPhones'
        db.delete_table('contacts_hs_contactphones')

        # Deleting model 'ContactEmail'
        db.delete_table('contacts_hs_contactemail')


    models = {
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'clients.client': {
            'Meta': {'object_name': 'Client'},
            'about': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'approval_rating': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_message': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'contacts_hs.contactemail': {
            'Meta': {'object_name': 'ContactEmail'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'emails'", 'to': "orm['contacts_hs.ContactInfo']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '42'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Other'", 'max_length': '42'})
        },
        'contacts_hs.contactgroup': {
            'Meta': {'object_name': 'ContactGroup'},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['contacts_hs.ContactInfo']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contacts_hs.contactinfo': {
            'Meta': {'object_name': 'ContactInfo'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clients.Client']", 'null': 'True', 'blank': 'True'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['friends.Contact']", 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_contacts'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'contacts_hs.contactphones': {
            'Meta': {'object_name': 'ContactPhones'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phone_numbers'", 'to': "orm['contacts_hs.ContactInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '42'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Mobile'", 'max_length': '42'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'friends.contact': {
            'Meta': {'object_name': 'Contact'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contacts'", 'to': "orm['auth.User']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'healers.healer': {
            'Meta': {'object_name': 'Healer', '_ormbases': ['clients.Client']},
            'bookAheadDays': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'client_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['clients.Client']", 'unique': 'True', 'primary_key': 'True'}),
            'defaultTimelsotLength': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'google_calendar_edit_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_calendar_feed_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'leadTime': ('django.db.models.fields.PositiveIntegerField', [], {'default': '24'}),
            'manualAppointmentConfirmation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'profileVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'scheduleUpdatedThrough': ('django.db.models.fields.DateField', [], {'default': "'1969-08-17'"}),
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'setup_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '30'})
        }
    }

    complete_apps = ['contacts_hs']
