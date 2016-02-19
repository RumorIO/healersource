# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0010_healer_gift_certificates_expiration_period_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='giftcertificate',
            name='amount',
            field=models.PositiveIntegerField(),
        ),
    ]
