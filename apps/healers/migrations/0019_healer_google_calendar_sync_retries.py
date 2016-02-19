# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0018_auto_20150114_0645'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='google_calendar_sync_retries',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
