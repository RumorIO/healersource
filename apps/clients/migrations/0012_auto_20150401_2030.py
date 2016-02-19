# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0011_auto_20150401_1803'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='phonegap_signup',
        ),
        migrations.AlterField(
            model_name='client',
            name='signup_source',
            field=models.CharField(default=b'homepage', max_length=32, null=True, blank=True, choices=[(b'notes_lp', b'Notes Landing Page'), (b'homepage', b'Homepage'), (b'app', b'App')]),
            preserve_default=True,
        ),
    ]
