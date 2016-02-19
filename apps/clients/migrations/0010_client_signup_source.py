# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='signup_source',
            field=models.CharField(blank=True, max_length=32, null=True, choices=[(b'notes_lp', b'Notes Landing Page'), (b'homepage', b'Homepage'), (b'referral', b'Referral'), (b'app', b'App')]),
            preserve_default=True,
        ),
    ]
