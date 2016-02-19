# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0016_auto_20150114_0638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='book_online',
        ),
    ]
