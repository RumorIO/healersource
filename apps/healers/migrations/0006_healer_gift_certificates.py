# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0005_healer_booking_payment_requirement'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='gift_certificates',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
