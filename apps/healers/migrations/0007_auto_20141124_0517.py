# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0006_healer_gift_certificates'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('purchased_for', models.CharField(max_length=100)),
                ('purchased_by', models.CharField(max_length=100)),
                ('amount', models.FloatField()),
                ('code', models.CharField(unique=True, max_length=6)),
                ('purchase_date', models.DateField(auto_now_add=True)),
                ('redeemed', models.BooleanField(default=False)),
                ('healer', models.ForeignKey(related_name=b'gift_certificates', to='healers.Healer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RenameField(
            model_name='healer',
            old_name='gift_certificates',
            new_name='gift_certificates_enabled',
        ),
    ]
