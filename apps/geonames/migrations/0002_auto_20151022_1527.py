# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geonames', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geoname',
            name='population',
            field=models.PositiveIntegerField(db_index=True),
            preserve_default=True,
        ),
    ]
