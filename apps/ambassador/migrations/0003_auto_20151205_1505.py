# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ambassador', '0002_auto_20150227_0846'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='level',
            options={'ordering': ['plan', 'level']},
        ),
    ]
