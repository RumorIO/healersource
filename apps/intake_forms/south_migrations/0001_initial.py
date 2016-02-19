# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'IntakeForm'
        db.create_table('intake_forms_intakeform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('healer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='intake_forms', to=orm['healers.Healer'])),
            ('answer_option', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal('intake_forms', ['IntakeForm'])

        # Adding model 'Question'
        db.create_table('intake_forms_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questions', to=orm['intake_forms.IntakeForm'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('answer_rows', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal('intake_forms', ['Question'])

        # Adding model 'Answer'
        db.create_table('intake_forms_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(related_name='intake_form_answers', to=orm['clients.Client'])),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['intake_forms.IntakeForm'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('intake_forms', ['Answer'])

        # Adding model 'AnswerResult'
        db.create_table('intake_forms_answerresult', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['intake_forms.Answer'])),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['intake_forms.Question'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('intake_forms', ['AnswerResult'])


    def backwards(self, orm):
        
        # Deleting model 'IntakeForm'
        db.delete_table('intake_forms_intakeform')

        # Deleting model 'Question'
        db.delete_table('intake_forms_question')

        # Deleting model 'Answer'
        db.delete_table('intake_forms_answer')

        # Deleting model 'AnswerResult'
        db.delete_table('intake_forms_answerresult')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 9, 25, 17, 4, 21, 826788)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 9, 25, 17, 4, 21, 826666)'}),
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
            'ratings_1_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_2_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_3_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_4_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_5_star': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ratings_average': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'review_permission': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'scheduleUpdatedThrough': ('django.db.models.fields.DateField', [], {'default': "'1969-08-17'"}),
            'scheduleVisibility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'seen_appointments_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seen_availability_help': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_notification': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'send_sms_appt_request': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'setup_step': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'setup_time': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '30'}),
            'smart_scheduler_avoid_gaps_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': "'6'", 'blank': 'True'}),
            'years_in_practice': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '4', 'blank': 'True'})
        },
        'intake_forms.answer': {
            'Meta': {'object_name': 'Answer'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intake_form_answers'", 'to': "orm['clients.Client']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['intake_forms.IntakeForm']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'intake_forms.answerresult': {
            'Meta': {'object_name': 'AnswerResult'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['intake_forms.Answer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['intake_forms.Question']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'intake_forms.intakeform': {
            'Meta': {'object_name': 'IntakeForm'},
            'answer_option': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'healer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intake_forms'", 'to': "orm['healers.Healer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'intake_forms.question': {
            'Meta': {'object_name': 'Question'},
            'answer_rows': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions'", 'to': "orm['intake_forms.IntakeForm']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['intake_forms']
