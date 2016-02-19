# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0014_auto_20141222_0310'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='booking_optional_message_allowed',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
