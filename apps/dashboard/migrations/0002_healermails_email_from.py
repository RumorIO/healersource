# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='healermails',
            name='email_from',
            field=models.EmailField(default=None, max_length=255, null=True),
            preserve_default=False,
        ),
    ]
