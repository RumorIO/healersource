# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0007_auto_20150312_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='is_deleted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
