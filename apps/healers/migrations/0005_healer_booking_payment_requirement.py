# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0004_auto_20141122_2032'),
    ]

    operations = [
        migrations.AddField(
            model_name='healer',
            name='booking_payment_requirement',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'Require full amount on booking'), (2, b"Require client to enter credit card on booking, but don't charge anything"), (3, b'Clients can book without credit card')]),
            preserve_default=True,
        ),
    ]
