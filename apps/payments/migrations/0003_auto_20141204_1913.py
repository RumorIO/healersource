# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_auto_20141202_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='currentsubscription',
            name='booking_active',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='currentsubscription',
            name='booking_status',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customer',
            name='payment_booking',
            field=models.FloatField(default=0),
            preserve_default=True,
        ),
    ]
