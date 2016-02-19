# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0022_auto_20150403_0730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healer',
            name='profile_completeness_reminder_interval',
            field=models.PositiveSmallIntegerField(default=4, choices=[(1, b'1 week'), (2, b'2 weeks'), (4, b'1 month'), (8, b'2 months')]),
            preserve_default=True,
        ),
    ]
