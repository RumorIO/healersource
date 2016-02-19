# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'Address', fields ['address_line2', 'city', 'address_line1', 'state_province', 'postal_code', 'country']
        db.delete_unique('healers_address', ['address_line2', 'city', 'address_line1', 'state_province', 'postal_code', 'country'])

        # Deleting field 'Address.address_line2'
        db.delete_column('healers_address', 'address_line2')

        # Deleting field 'Address.city'
        db.delete_column('healers_address', 'city')

        # Deleting field 'Address.postal_code'
        db.delete_column('healers_address', 'postal_code')

        # Deleting field 'Address.address_line1'
        db.delete_column('healers_address', 'address_line1')

        # Deleting field 'Address.state_province'
        db.delete_column('healers_address', 'state_province')

        # Deleting field 'Address.country'
        db.delete_column('healers_address', 'country')


    def backwards(self, orm):
        
        # Adding field 'Address.address_line2'
        db.add_column('healers_address', 'address_line2', self.gf('django.db.models.fields.CharField')(default='', max_length=42, blank=True), keep_default=False)

        # Adding field 'Address.city'
        db.add_column('healers_address', 'city', self.gf('django.db.models.fields.CharField')(default='', max_length=42), keep_default=False)

        # Adding field 'Address.postal_code'
        db.add_column('healers_address', 'postal_code', self.gf('django.db.models.fields.CharField')(default='', max_length=10), keep_default=False)

        # Adding field 'Address.address_line1'
        db.add_column('healers_address', 'address_line1', self.gf('django.db.models.fields.CharField')(default='', max_length=42), keep_default=False)

        # Adding field 'Address.state_province'
        db.add_column('healers_address', 'state_province', self.gf('django.db.models.fields.CharField')(default='', max_length=42, blank=True), keep_default=False)

        # Adding field 'Address.country'
        db.add_column('healers_address', 'country', self.gf('django.db.models.fields.CharField')(default='', max_length=42, blank=True), keep_default=False)

        # Adding unique constraint on 'Address', fields ['address_line2', 'city', 'address_line1', 'state_province', 'postal_code', 'country']
        db.create_unique('healers_address', ['address_line2', 'city', 'address_line1', 'state_province', 'postal_code', 'country'])


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'friends.friendship': {
            'Meta': {'unique_together': "(('to_user', 'from_user'),)", 'object_name': 'Friendship'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_unused_'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'friends'", 'to': "orm['auth.User']"})
        },
        'friends.friendshipinvitation': {
            'Meta': {'object_name': 'FriendshipInvitation'},
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_from'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'sent': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_to'", 'to': "orm['auth.User']"})
        },
        'healers.address': {
            'Meta': {'object_name': 'Address'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'healers.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'base_appointment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Appointment']", 'null': 'True', 'blank': 'True'}),
            'canceled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clients.Client']"}),
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'google_event_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_appointments'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Location']", 'null': 'True'}),
            'repeat_end_after': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'weekly': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'healers.clientinvitation': {
            'Meta': {'object_name': 'ClientInvitation', '_ormbases': ['friends.FriendshipInvitation']},
            'friendshipinvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.FriendshipInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.clients': {
            'Meta': {'object_name': 'Clients', '_ormbases': ['friends.Friendship']},
            'friendship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.Friendship']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.healer': {
            'Meta': {'object_name': 'Healer', '_ormbases': ['clients.Client']},
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bookAheadDays': ('django.db.models.fields.IntegerField', [], {'default': '30'}),
            'client_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['clients.Client']", 'unique': 'True', 'primary_key': 'True'}),
            'defaultTimelsotLength': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'google_calendar_edit_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_calendar_feed_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'leadTime': ('django.db.models.fields.PositiveIntegerField', [], {'default': '24'}),
            'manualAppointmentConfirmation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'profileVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'scheduleUpdatedThrough': ('django.db.models.fields.DateField', [], {'default': "'1969-08-17'"}),
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        'healers.healerlocation': {
            'Meta': {'object_name': 'HealerLocation'},
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Location']"})
        },
        'healers.healertimeslot': {
            'Meta': {'object_name': 'HealerTimeslot'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Location']", 'null': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'weekly': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'healers.location': {
            'Meta': {'object_name': 'Location', '_ormbases': ['healers.Address']},
            'address_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['healers.Address']", 'unique': 'True', 'primary_key': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Room']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'})
        },
        'healers.referralinvitation': {
            'Meta': {'object_name': 'ReferralInvitation', '_ormbases': ['friends.FriendshipInvitation']},
            'friendshipinvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.FriendshipInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.referrals': {
            'Meta': {'object_name': 'Referrals', '_ormbases': ['friends.Friendship']},
            'friendship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.Friendship']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.room': {
            'Meta': {'object_name': 'Room'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        },
        'healers.vacation': {
            'Meta': {'object_name': 'Vacation'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'weekly': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['healers']
