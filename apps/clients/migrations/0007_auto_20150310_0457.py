# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_auto_20150307_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='embed_background_color',
            field=models.CharField(max_length=7, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='embed_search_all',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
