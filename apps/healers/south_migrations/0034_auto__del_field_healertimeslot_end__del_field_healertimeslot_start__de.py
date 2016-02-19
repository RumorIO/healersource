# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'HealerTimeslot.end'
        db.delete_column('healers_healertimeslot', 'end')

        # Deleting field 'HealerTimeslot.start'
        db.delete_column('healers_healertimeslot', 'start')

        # Deleting field 'HealerTimeslot.weekly'
        db.delete_column('healers_healertimeslot', 'weekly')

        # Adding field 'HealerTimeslot.start_date'
        db.add_column('healers_healertimeslot', 'start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2011, 5, 18)), keep_default=False)

        # Adding field 'HealerTimeslot.end_date'
        db.add_column('healers_healertimeslot', 'end_date', self.gf('django.db.models.fields.DateField')(null=True), keep_default=False)

        # Adding field 'HealerTimeslot.start_time'
        db.add_column('healers_healertimeslot', 'start_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'HealerTimeslot.end_time'
        db.add_column('healers_healertimeslot', 'end_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'HealerTimeslot.repeat_period'
        db.add_column('healers_healertimeslot', 'repeat_period', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=None, null=True), keep_default=False)

        # Adding field 'HealerTimeslot.repeat_every'
        db.add_column('healers_healertimeslot', 'repeat_every', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, null=True), keep_default=False)

        # Adding field 'HealerTimeslot.exceptions'
        db.add_column('healers_healertimeslot', 'exceptions', self.gf('healers.fields.SeparatedValuesField')(null=True), keep_default=False)

        # Deleting field 'Appointment.end'
        db.delete_column('healers_appointment', 'end')

        # Deleting field 'Appointment.start'
        db.delete_column('healers_appointment', 'start')

        # Deleting field 'Appointment.weekly'
        db.delete_column('healers_appointment', 'weekly')

        # Adding field 'Appointment.start_date'
        db.add_column('healers_appointment', 'start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2011, 5, 18)), keep_default=False)

        # Adding field 'Appointment.end_date'
        db.add_column('healers_appointment', 'end_date', self.gf('django.db.models.fields.DateField')(null=True), keep_default=False)

        # Adding field 'Appointment.start_time'
        db.add_column('healers_appointment', 'start_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'Appointment.end_time'
        db.add_column('healers_appointment', 'end_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'Appointment.exceptions'
        db.add_column('healers_appointment', 'exceptions', self.gf('healers.fields.SeparatedValuesField')(null=True), keep_default=False)

        # Deleting field 'Vacation.end'
        db.delete_column('healers_vacation', 'end')

        # Deleting field 'Vacation.start'
        db.delete_column('healers_vacation', 'start')

        # Deleting field 'Vacation.weekly'
        db.delete_column('healers_vacation', 'weekly')

        # Adding field 'Vacation.start_date'
        db.add_column('healers_vacation', 'start_date', self.gf('django.db.models.fields.DateField')(default=datetime.date(2011, 5, 18)), keep_default=False)

        # Adding field 'Vacation.end_date'
        db.add_column('healers_vacation', 'end_date', self.gf('django.db.models.fields.DateField')(null=True), keep_default=False)

        # Adding field 'Vacation.start_time'
        db.add_column('healers_vacation', 'start_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'Vacation.end_time'
        db.add_column('healers_vacation', 'end_time', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0), keep_default=False)

        # Adding field 'Vacation.repeat_period'
        db.add_column('healers_vacation', 'repeat_period', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=None, null=True), keep_default=False)

        # Adding field 'Vacation.repeat_every'
        db.add_column('healers_vacation', 'repeat_every', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, null=True), keep_default=False)

        # Adding field 'Vacation.exceptions'
        db.add_column('healers_vacation', 'exceptions', self.gf('healers.fields.SeparatedValuesField')(null=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'HealerTimeslot.end'
        db.add_column('healers_healertimeslot', 'end', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 31, 31, 701170), db_index=True), keep_default=False)

        # Adding field 'HealerTimeslot.start'
        db.add_column('healers_healertimeslot', 'start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 31, 49, 450426), db_index=True), keep_default=False)

        # Adding field 'HealerTimeslot.weekly'
        db.add_column('healers_healertimeslot', 'weekly', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Deleting field 'HealerTimeslot.start_date'
        db.delete_column('healers_healertimeslot', 'start_date')

        # Deleting field 'HealerTimeslot.end_date'
        db.delete_column('healers_healertimeslot', 'end_date')

        # Deleting field 'HealerTimeslot.start_time'
        db.delete_column('healers_healertimeslot', 'start_time')

        # Deleting field 'HealerTimeslot.end_time'
        db.delete_column('healers_healertimeslot', 'end_time')

        # Deleting field 'HealerTimeslot.repeat_period'
        db.delete_column('healers_healertimeslot', 'repeat_period')

        # Deleting field 'HealerTimeslot.repeat_every'
        db.delete_column('healers_healertimeslot', 'repeat_every')

        # Deleting field 'HealerTimeslot.exceptions'
        db.delete_column('healers_healertimeslot', 'exceptions')

        # Adding field 'Appointment.end'
        db.add_column('healers_appointment', 'end', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 32, 53, 775616), db_index=True), keep_default=False)

        # Adding field 'Appointment.start'
        db.add_column('healers_appointment', 'start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 33, 14, 738885), db_index=True), keep_default=False)

        # Adding field 'Appointment.weekly'
        db.add_column('healers_appointment', 'weekly', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Deleting field 'Appointment.start_date'
        db.delete_column('healers_appointment', 'start_date')

        # Deleting field 'Appointment.end_date'
        db.delete_column('healers_appointment', 'end_date')

        # Deleting field 'Appointment.start_time'
        db.delete_column('healers_appointment', 'start_time')

        # Deleting field 'Appointment.end_time'
        db.delete_column('healers_appointment', 'end_time')

        # Deleting field 'Appointment.exceptions'
        db.delete_column('healers_appointment', 'exceptions')

        # Adding field 'Vacation.end'
        db.add_column('healers_vacation', 'end', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 31, 31, 701170), db_index=True), keep_default=False)

        # Adding field 'Vacation.start'
        db.add_column('healers_vacation', 'start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 5, 18, 9, 31, 31, 701170), db_index=True), keep_default=False)

        # Adding field 'Vacation.weekly'
        db.add_column('healers_vacation', 'weekly', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Deleting field 'Vacation.start_date'
        db.delete_column('healers_vacation', 'start_date')

        # Deleting field 'Vacation.end_date'
        db.delete_column('healers_vacation', 'end_date')

        # Deleting field 'Vacation.start_time'
        db.delete_column('healers_vacation', 'start_time')

        # Deleting field 'Vacation.end_time'
        db.delete_column('healers_vacation', 'end_time')

        # Deleting field 'Vacation.repeat_period'
        db.delete_column('healers_vacation', 'repeat_period')

        # Deleting field 'Vacation.repeat_every'
        db.delete_column('healers_vacation', 'repeat_every')

        # Deleting field 'Vacation.exceptions'
        db.delete_column('healers_vacation', 'exceptions')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'referred_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
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
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'})
        },
        'healers.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'base_appointment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['healers.Appointment']", 'null': 'True', 'blank': 'True'}),
            'canceled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['clients.Client']"}),
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'google_event_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_appointments'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['healers.Location']", 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'repeat_end_after': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
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
            'beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
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
            'address_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['healers.Address']", 'unique': 'True', 'primary_key': 'True'}),
            'room': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
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
        }
    }

    complete_apps = ['healers']
