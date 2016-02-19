# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client_notes', '0006_auto_20150317_1528'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diagram',
            options={'ordering': ['order']},
        ),
    ]
