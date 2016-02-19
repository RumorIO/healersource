# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0013_auto_20141204_1737'),
    ]

    operations = [
        migrations.AddField(
            model_name='wellnesscenter',
            name='common_availability',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
