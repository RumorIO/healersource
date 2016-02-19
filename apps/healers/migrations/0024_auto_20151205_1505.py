# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0023_auto_20151013_2217'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healer',
            name='google_email',
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
