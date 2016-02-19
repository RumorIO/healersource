# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0019_healer_google_calendar_sync_retries'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='healer',
            name='notes_notice_shown',
        ),
    ]
