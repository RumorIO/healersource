# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sync_hs', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unavailablecalendar',
            old_name='feed_link',
            new_name='calendar_id',
        ),
    ]
