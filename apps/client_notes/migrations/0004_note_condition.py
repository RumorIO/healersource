# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client_notes', '0004_auto_20141210_0400'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='condition',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
