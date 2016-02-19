# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20141204_1913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='payment_booking',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='customer',
            name='payment_notes',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='customer',
            name='payment_schedule',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
