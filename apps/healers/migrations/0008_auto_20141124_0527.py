# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0007_auto_20141124_0517'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='gift_certificates_expiration_period',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='healer',
            name='gift_certificates_expiration_period_type',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
