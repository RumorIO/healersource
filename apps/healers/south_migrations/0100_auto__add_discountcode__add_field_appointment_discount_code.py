# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DiscountCode'
        db.create_table(u'healers_discountcode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('healer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='discount_codes', to=orm['healers.Healer'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('amount', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('type', self.gf('django.db.models.fields.CharField')(default='$', max_length=1)),
        ))
        db.send_create_signal(u'healers', ['DiscountCode'])

        # Adding field 'Appointment.discount_code'
        db.add_column(u'healers_appointment', 'discount_code',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['healers.DiscountCode'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'DiscountCode'
        db.delete_table(u'healers_discountcode')

        # Deleting field 'Appointment.discount_code'
        db.delete_column(u'healers_appointment', 'discount_code_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'clients.client': {
            'Meta': {'object_name': 'Client'},
            'about': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'approval_rating': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'datetime.datetime.now', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'first_login': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'google_plus': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_message': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'link_source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'linkedin': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'referred_by': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'send_reminders': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'friends.friendship': {
            'Meta': {'unique_together': "(('to_user', 'from_user'),)", 'object_name': 'Friendship'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_unused_'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'friends'", 'to': u"orm['auth.User']"})
        },
        u'friends.friendshipinvitation': {
            'Meta': {'object_name': 'FriendshipInvitation'},
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_from'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'sent': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_to'", 'to': u"orm['auth.User']"})
        },
        u'healers.address': {
            'Meta': {'object_name': 'Address'},
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'blank': 'True'}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '42', 'blank': 'True'})
        },
        u'healers.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'base_appointment': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['healers.Appointment']", 'null': 'True'}),
            'canceled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['clients.Client']"}),
            'confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_appts'", 'to': u"orm['auth.User']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {}),
            'discount_code': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.DiscountCode']", 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'google_event_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_appointments'", 'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'modified_appts'", 'to': u"orm['auth.User']"}),
            'last_modified_date': ('django.db.models.fields.DateTimeField', [], {}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['healers.Location']", 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'repeat_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['healers.Room']", 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'treatment_length': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['healers.TreatmentTypeLength']", 'null': 'True'})
        },
        u'healers.clientinvitation': {
            'Meta': {'object_name': 'ClientInvitation', '_ormbases': [u'friends.FriendshipInvitation']},
            u'friendshipinvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['friends.FriendshipInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'healers.clients': {
            'Meta': {'object_name': 'Clients', '_ormbases': [u'friends.Friendship']},
            u'friendship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['friends.Friendship']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'healers.discountcode': {
            'Meta': {'ordering': "['code']", 'object_name': 'DiscountCode'},
            'amount': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'discount_codes'", 'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'$'", 'max_length': '1'})
        },
        u'healers.healer': {
            'Meta': {'object_name': 'Healer', '_ormbases': [u'clients.Client']},
            'additional_text_for_email': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'bookAheadDays': ('django.db.models.fields.IntegerField', [], {'default': '90'}),
            'cancellation_policy': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'client_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['clients.Client']", 'unique': 'True', 'primary_key': 'True'}),
            'client_screening': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'defaultTimeslotLength': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'default_location': ('django.db.models.fields.CharField', [], {'default': "'USA'", 'max_length': '64'}),
            'default_modality': ('django.db.models.fields.CharField', [], {'default': "'Healer'", 'max_length': '64'}),
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
            'profile_completeness_reminder_interval': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'profile_completeness_reminder_lastdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'ratings_1_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_2_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_3_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_4_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_5_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_average': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'review_permission': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'scheduleUpdatedThrough': ('django.db.models.fields.DateField', [], {'default': "'1969-08-17'"}),
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'schedule_full_width': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_start_from_sunday_setting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seen_appointments_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seen_availability_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_notification': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'send_sms_appt_request': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'setup_step': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'setup_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '30'}),
            'smart_scheduler_avoid_gaps_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': "'6'", 'blank': 'True'}),
            'wellness_center_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['healers.WellnessCenter']", 'null': 'True', 'blank': 'True'}),
            'years_in_practice': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'})
        },
        u'healers.healertimeslot': {
            'Meta': {'object_name': 'HealerTimeslot'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['healers.Location']", 'null': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'healers.location': {
            'Meta': {'object_name': 'Location', '_ormbases': [u'healers.Address']},
            'addressVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            u'address_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['healers.Address']", 'unique': 'True', 'primary_key': 'True'}),
            'book_online': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'color': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '7'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': "'6'", 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '42'})
        },
        u'healers.referralinvitation': {
            'Meta': {'object_name': 'ReferralInvitation', '_ormbases': [u'friends.FriendshipInvitation']},
            u'friendshipinvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['friends.FriendshipInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'healers.referrals': {
            'Meta': {'object_name': 'Referrals', '_ormbases': [u'friends.Friendship']},
            u'friendship_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['friends.Friendship']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'healers.room': {
            'Meta': {'ordering': "['name']", 'object_name': 'Room'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rooms'", 'to': u"orm['healers.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'healers.treatmenttype': {
            'Meta': {'object_name': 'TreatmentType'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'healer_treatment_types'", 'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rooms': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'treatment_types'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['healers.Room']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '42'})
        },
        u'healers.treatmenttypelength': {
            'Meta': {'ordering': "['length']", 'object_name': 'TreatmentTypeLength'},
            'cost': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'treatment_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lengths'", 'to': u"orm['healers.TreatmentType']"})
        },
        u'healers.unavailableslot': {
            'Meta': {'object_name': 'UnavailableSlot'},
            'api': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sync_hs.UnavailableCalendar']", 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'event_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        u'healers.vacation': {
            'Meta': {'object_name': 'Vacation'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'end_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'exceptions': ('healers.fields.SeparatedValuesField', [], {'null': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'repeat_every': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'repeat_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': 'None', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'healers.wellnesscenter': {
            'Meta': {'object_name': 'WellnessCenter', '_ormbases': [u'healers.Healer']},
            u'healer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['healers.Healer']", 'unique': 'True', 'primary_key': 'True'}),
            'payment_schedule_setting': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'schedule_dropdown_provider_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_side_by_side_setting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_trial_started_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'healers.wellnesscentergoogleeventlink': {
            'Meta': {'object_name': 'WellnessCenterGoogleEventLink'},
            'appointment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wellness_center_google_event_links'", 'to': u"orm['healers.Appointment']"}),
            'google_event_link': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'wellness_center': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.WellnessCenter']"})
        },
        u'healers.wellnesscentertreatmenttype': {
            'Meta': {'object_name': 'WellnessCenterTreatmentType'},
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wellness_center_treatment_types'", 'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'treatment_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['healers.TreatmentType']", 'null': 'True', 'blank': 'True'}),
            'wellness_center': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.WellnessCenter']"})
        },
        u'healers.zipcode': {
            'Meta': {'object_name': 'Zipcode'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'population': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'})
        },
        u'sync_hs.unavailablecalendar': {
            'Meta': {'object_name': 'UnavailableCalendar'},
            'api': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'feed_link': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['healers']