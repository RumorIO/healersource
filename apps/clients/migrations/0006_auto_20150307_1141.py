# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_auto_20150225_0502'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='ambassador_homepage',
            new_name='ambassador_program',
        ),
    ]
