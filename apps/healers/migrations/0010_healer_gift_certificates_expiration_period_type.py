# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0009_remove_healer_gift_certificates_expiration_period_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='gift_certificates_expiration_period_type',
            field=models.PositiveSmallIntegerField(default=3, choices=[(1, b'days'), (2, b'months'), (3, b'years')]),
            preserve_default=True,
        ),
    ]
