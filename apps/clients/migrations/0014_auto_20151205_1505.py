# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0013_client_yelp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='date_modified',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
