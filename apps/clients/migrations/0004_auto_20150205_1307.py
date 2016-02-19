# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_auto_20150119_1136'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='phonegap_signup',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
