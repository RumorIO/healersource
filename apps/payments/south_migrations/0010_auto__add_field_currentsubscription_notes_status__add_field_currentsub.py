# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CurrentSubscription.notes_status'
        db.add_column(u'payments_currentsubscription', 'notes_status',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'CurrentSubscription.notes_active'
        db.add_column(u'payments_currentsubscription', 'notes_active',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Customer.payment_notes'
        db.add_column(u'payments_customer', 'payment_notes',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CurrentSubscription.notes_status'
        db.delete_column(u'payments_currentsubscription', 'notes_status')

        # Deleting field 'CurrentSubscription.notes_active'
        db.delete_column(u'payments_currentsubscription', 'notes_active')

        # Deleting field 'Customer.payment_notes'
        db.delete_column(u'payments_customer', 'payment_notes')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'payments.charge': {
            'Meta': {'object_name': 'Charge'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'amount_refunded': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'card_kind': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'card_last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'charge_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charges'", 'to': u"orm['payments.Customer']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'disputed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charges'", 'null': 'True', 'to': u"orm['payments.Invoice']"}),
            'paid': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'receipt_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'refunded': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'payments.currentsubscription': {
            'Meta': {'object_name': 'CurrentSubscription'},
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'current_subscription'", 'unique': 'True', 'null': 'True', 'to': u"orm['payments.Customer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notes_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'payments.customer': {
            'Meta': {'object_name': 'Customer'},
            'card_fingerprint': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'card_kind': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'card_last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_purged': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_notes': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'payment_schedule': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'null': 'True'})
        },
        u'payments.event': {
            'Meta': {'object_name': 'Event'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Customer']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'livemode': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'valid': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'validated_message': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'webhook_message': ('jsonfield.fields.JSONField', [], {'default': '{}'})
        },
        u'payments.eventprocessingexception': {
            'Meta': {'object_name': 'EventProcessingException'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Event']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'traceback': ('django.db.models.fields.TextField', [], {})
        },
        u'payments.invoice': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Invoice'},
            'attempted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'attempts': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'charge': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoices'", 'to': u"orm['payments.Customer']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'period_end': ('django.db.models.fields.DateTimeField', [], {}),
            'period_start': ('django.db.models.fields.DateTimeField', [], {}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subtotal': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'})
        },
        u'payments.invoiceitem': {
            'Meta': {'object_name': 'InvoiceItem'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['payments.Invoice']"}),
            'line_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'period_end': ('django.db.models.fields.DateTimeField', [], {}),
            'period_start': ('django.db.models.fields.DateTimeField', [], {}),
            'plan': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'proration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'payments.transfer': {
            'Meta': {'object_name': 'Transfer'},
            'adjustment_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'adjustment_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'adjustment_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'charge_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'charge_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'charge_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'collected_fee_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'collected_fee_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transfers'", 'to': u"orm['payments.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'net': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'refund_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'refund_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'refund_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'validation_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'validation_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2'})
        },
        u'payments.transferchargefee': {
            'Meta': {'object_name': 'TransferChargeFee'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'application': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'transfer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charge_fee_details'", 'to': u"orm['payments.Transfer']"})
        }
    }

    complete_apps = ['payments']