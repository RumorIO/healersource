# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ClientVideo.order'
        db.add_column(u'clients_clientvideo', 'order',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'ClientVideo.videotype'
        db.add_column(u'clients_clientvideo', 'videotype',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ClientVideo.order'
        db.delete_column(u'clients_clientvideo', 'order')

        # Deleting field 'ClientVideo.videotype'
        db.delete_column(u'clients_clientvideo', 'videotype')


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
        u'clients.clientlocation': {
            'Meta': {'ordering': "['location']", 'object_name': 'ClientLocation'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['clients.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['healers.Location']"})
        },
        u'clients.clientphonenumber': {
            'Meta': {'object_name': 'ClientPhoneNumber'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'phone_numbers'", 'to': u"orm['clients.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '42'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Mobile'", 'max_length': '42'})
        },
        u'clients.clientvideo': {
            'Meta': {'ordering': "['-date_added']", 'object_name': 'ClientVideo'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'to': u"orm['clients.Client']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'video_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'videotype': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'clients.referralssent': {
            'Meta': {'unique_together': "(('provider_user', 'client_user', 'referring_user'),)", 'object_name': 'ReferralsSent'},
            'client_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'null': 'True'}),
            'client_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'referral_client'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'date_sent': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'provider_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'referral_provider'", 'to': u"orm['auth.User']"}),
            'referring_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'referral_sender'", 'to': u"orm['auth.User']"}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        u'clients.sitejoininvitation': {
            'Meta': {'object_name': 'SiteJoinInvitation', '_ormbases': [u'friends.JoinInvitation']},
            'create_friendship': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_from_site': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_to_healer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'joininvitation_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['friends.JoinInvitation']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'friends.contact': {
            'Meta': {'object_name': 'Contact'},
            'added': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contacts'", 'to': u"orm['auth.User']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'friends.joininvitation': {
            'Meta': {'object_name': 'JoinInvitation'},
            'confirmation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['friends.Contact']"}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'join_from'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'sent': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'})
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
        }
    }

    complete_apps = ['clients']