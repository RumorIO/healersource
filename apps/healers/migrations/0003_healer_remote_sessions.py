# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0002_auto_20141107_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='remote_sessions',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
