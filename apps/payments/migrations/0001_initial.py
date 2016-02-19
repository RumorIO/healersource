# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import __builtin__
import jsonfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('card_last_4', models.CharField(max_length=4, blank=True)),
                ('card_kind', models.CharField(max_length=50, blank=True)),
                ('amount', models.DecimalField(null=True, max_digits=7, decimal_places=2)),
                ('amount_refunded', models.DecimalField(null=True, max_digits=7, decimal_places=2)),
                ('description', models.TextField(blank=True)),
                ('paid', models.NullBooleanField()),
                ('disputed', models.NullBooleanField()),
                ('refunded', models.NullBooleanField()),
                ('fee', models.DecimalField(null=True, max_digits=7, decimal_places=2)),
                ('receipt_sent', models.BooleanField(default=False)),
                ('charge_created', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CurrentSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('schedule_status', models.BooleanField(default=False)),
                ('schedule_active', models.BooleanField(default=False)),
                ('notes_status', models.BooleanField(default=False)),
                ('notes_active', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('card_fingerprint', models.CharField(max_length=200, blank=True)),
                ('card_last_4', models.CharField(max_length=4, blank=True)),
                ('card_kind', models.CharField(max_length=50, blank=True)),
                ('card_stripe_id', models.CharField(max_length=255)),
                ('date_purged', models.DateTimeField(null=True, editable=False)),
                ('payment_schedule', models.FloatField(default=0)),
                ('payment_notes', models.FloatField(default=0)),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(max_length=255)),
                ('attempted', models.NullBooleanField()),
                ('attempts', models.PositiveIntegerField(null=True)),
                ('closed', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('period_end', models.DateTimeField()),
                ('period_start', models.DateTimeField()),
                ('subtotal', models.DecimalField(max_digits=7, decimal_places=2)),
                ('total', models.DecimalField(max_digits=7, decimal_places=2)),
                ('date', models.DateTimeField()),
                ('charge', models.CharField(max_length=50, blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('customer', models.ForeignKey(related_name=b'invoices', to='payments.Customer')),
            ],
            options={
                'ordering': ['-date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(max_digits=7, decimal_places=2)),
                ('currency', models.CharField(max_length=10)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('proration', models.BooleanField(default=False)),
                ('line_type', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200, blank=True)),
                ('plan', models.CharField(max_length=100, blank=True)),
                ('quantity', models.IntegerField(null=True)),
                ('invoice', models.ForeignKey(related_name=b'items', to='payments.Invoice')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('date', models.DateField()),
                ('amount', models.FloatField()),
                ('paid', models.BooleanField(default=False)),
                ('appointment', models.ForeignKey(related_name=b'payments', to='healers.Appointment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('kind', models.CharField(max_length=250)),
                ('livemode', models.BooleanField(default=False)),
                ('webhook_message', jsonfield.fields.JSONField(default=__builtin__.dict)),
                ('validated_message', jsonfield.fields.JSONField(null=True)),
                ('valid', models.NullBooleanField()),
                ('processed', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(to='payments.Customer', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentEventProcessingException',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.TextField()),
                ('message', models.CharField(max_length=500)),
                ('traceback', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('event', models.ForeignKey(to='payments.PaymentEvent', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='currentsubscription',
            name='customer',
            field=models.OneToOneField(related_name=b'current_subscription', null=True, to='payments.Customer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='charge',
            name='customer',
            field=models.ForeignKey(related_name=b'charges', to='payments.Customer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='charge',
            name='invoice',
            field=models.ForeignKey(related_name=b'charges', to='payments.Invoice', null=True),
            preserve_default=True,
        ),
    ]
