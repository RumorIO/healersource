# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0012_auto_20150401_2030'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='yelp',
            field=models.CharField(default=b'', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
