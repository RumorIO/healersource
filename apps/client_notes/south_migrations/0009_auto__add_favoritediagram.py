# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FavoriteDiagram'
        db.create_table(u'client_notes_favoritediagram', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('healer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['healers.Healer'])),
        ))
        db.send_create_signal(u'client_notes', ['FavoriteDiagram'])

        # Adding M2M table for field diagrams on 'FavoriteDiagram'
        db.create_table(u'client_notes_favoritediagram_diagrams', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('favoritediagram', models.ForeignKey(orm[u'client_notes.favoritediagram'], null=False)),
            ('diagram', models.ForeignKey(orm[u'client_notes.diagram'], null=False))
        ))
        db.create_unique(u'client_notes_favoritediagram_diagrams', ['favoritediagram_id', 'diagram_id'])


    def backwards(self, orm):
        # Deleting model 'FavoriteDiagram'
        db.delete_table(u'client_notes_favoritediagram')

        # Removing M2M table for field diagrams on 'FavoriteDiagram'
        db.delete_table('client_notes_favoritediagram_diagrams')


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
        u'client_notes.diagram': {
            'Meta': {'object_name': 'Diagram'},
            'code_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['client_notes.Section']"})
        },
        u'client_notes.dot': {
            'Meta': {'object_name': 'Dot'},
            'diagram': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'diagrams'", 'to': u"orm['client_notes.Diagram']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'markers'", 'to': u"orm['client_notes.Marker']"}),
            'note': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dots'", 'to': u"orm['client_notes.Note']"}),
            'position_x': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'position_y': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'})
        },
        u'client_notes.favoritediagram': {
            'Meta': {'object_name': 'FavoriteDiagram'},
            'diagrams': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['client_notes.Diagram']", 'null': 'True', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'client_notes.marker': {
            'Meta': {'object_name': 'Marker'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'client_notes.note': {
            'Meta': {'ordering': "['-pk']", 'object_name': 'Note'},
            'assessment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '250'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['clients.Client']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finalized_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': u"orm['healers.Healer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'objective': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '250'}),
            'plan': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '250'}),
            'subjective': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '250'})
        },
        u'client_notes.section': {
            'Meta': {'object_name': 'Section'},
            'code_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        u'healers.wellnesscenter': {
            'Meta': {'object_name': 'WellnessCenter', '_ormbases': [u'healers.Healer']},
            u'healer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['healers.Healer']", 'unique': 'True', 'primary_key': 'True'}),
            'payment_schedule_setting': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'schedule_dropdown_provider_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_side_by_side_setting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_trial_started_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['client_notes']