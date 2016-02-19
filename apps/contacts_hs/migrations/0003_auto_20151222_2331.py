# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts_hs', '0002_auto_20141107_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinfo',
            name='address_line1',
            field=models.CharField(max_length=42, verbose_name=b'Address Line 1', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='address_line2',
            field=models.CharField(max_length=42, verbose_name=b'Address Line 2', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='city',
            field=models.CharField(max_length=42, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='country',
            field=models.CharField(max_length=42, verbose_name=b'Country', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='postal_code',
            field=models.CharField(db_index=True, max_length=10, verbose_name=b'Zip Code', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactinfo',
            name='state_province',
            field=models.CharField(max_length=42, verbose_name=b'State', blank=True),
            preserve_default=True,
        ),
    ]
