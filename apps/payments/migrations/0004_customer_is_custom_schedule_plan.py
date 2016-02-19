# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20141204_1913'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='is_custom_schedule_plan',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
