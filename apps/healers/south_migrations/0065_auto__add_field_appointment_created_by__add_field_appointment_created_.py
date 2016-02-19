# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Appointment.created_by'
        db.add_column('healers_appointment', 'created_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='created_appts', null=True, to=orm['auth.User']), keep_default=False)

        # Adding field 'Appointment.created_date'
        db.add_column('healers_appointment', 'created_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'Appointment.last_modified_by'
        db.add_column('healers_appointment', 'last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='modified_appts', null=True, to=orm['auth.User']), keep_default=False)

        # Adding field 'Appointment.last_modified_date'
        db.add_column('healers_appointment', 'last_modified_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

    def backwards(self, orm):
        
        # Deleting field 'Appointment.created_by'
        db.delete_column('healers_appointment', 'created_by_id')

        # Deleting field 'Appointment.created_date'
        db.delete_column('healers_appointment', 'created_date')

        # Deleting field 'Appointment.last_modified_by'
        db.delete_column('healers_appointment', 'last_modified_by_id')

        # Deleting field 'Appointment.last_modified_date'
        db.delete_column('healers_appointment', 'last_modified_date')


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
            'facebook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'first_login': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'google_plus': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_message': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'linkedin': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'send_reminders': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
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
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'})
        },
        'healers.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'base_appointment': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Appointment']", 'null': 'True'}),
            'canceled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clients.Client']"}),
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_appts'", 'null': 'True', 'to': "orm['auth.User']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'google_event_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_appointments'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'modified_appts'", 'null': 'True', 'to': "orm['auth.User']"}),
            'last_modified_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Location']", 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'repeat_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'treatment_length': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.TreatmentTypeLength']", 'null': 'True'})
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
            'additional_text_for_email': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'bookAheadDays': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'cancellation_policy': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'client_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['clients.Client']", 'unique': 'True', 'primary_key': 'True'}),
            'client_screening': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'defaultTimelsotLength': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'google_calendar_edit_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_calendar_feed_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'google_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'leadTime': ('django.db.models.fields.PositiveIntegerField', [], {'default': '24'}),
            'location_bar_title': ('django.db.models.fields.CharField', [], {'default': "'Locations: '", 'max_length': '36', 'blank': 'True'}),
            'manualAppointmentConfirmation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'office_hours_end': ('django.db.models.fields.TimeField', [], {'default': "'20:00:00'"}),
            'office_hours_start': ('django.db.models.fields.TimeField', [], {'default': "'10:00:00'"}),
            'phonesVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'profileVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'scheduleUpdatedThrough': ('django.db.models.fields.DateField', [], {'default': "'1969-08-17'"}),
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'seen_appointments_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seen_availability_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_notification': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'setup_step': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'setup_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '30'}),
            'smart_scheduler_avoid_gaps_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': "'6'", 'blank': 'True'}),
            'years_in_practice': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'})
        },
        'healers.healertimeslot': {
            'Meta': {'object_name': 'HealerTimeslot'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Location']", 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'healers.location': {
            'Meta': {'object_name': 'Location', '_ormbases': ['healers.Address']},
            'addressVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'address_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['healers.Address']", 'unique': 'True', 'primary_key': 'True'}),
            'book_online': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'room': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': "'6'", 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '42'})
        },
        'healers.referralinvitation': {
            'Meta': {'object_name': 'ReferralInvitation', '_ormbases': ['friends.FriendshipInvitation']},
            'friendshipinvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.FriendshipInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.referrals': {
            'Meta': {'object_name': 'Referrals', '_ormbases': ['friends.Friendship']},
            'friendship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['friends.Friendship']", 'unique': 'True', 'primary_key': 'True'})
        },
        'healers.treatmenttype': {
            'Meta': {'object_name': 'TreatmentType'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_treatment_types'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '42'})
        },
        'healers.treatmenttypelength': {
            'Meta': {'ordering': "['length']", 'object_name': 'TreatmentTypeLength'},
            'cost': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'treatment_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lengths'", 'to': "orm['healers.TreatmentType']"})
        },
        'healers.unavailableslot': {
            'Meta': {'object_name': 'UnavailableSlot'},
            'api': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sync_hs.UnavailableCalendar']", 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'event_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'healers.vacation': {
            'Meta': {'object_name': 'Vacation'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'healers.zipcode': {
            'Meta': {'object_name': 'Zipcode'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'population': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'})
        },
        'sync_hs.unavailablecalendar': {
            'Meta': {'object_name': 'UnavailableCalendar'},
            'api': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'feed_link': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['healers']
