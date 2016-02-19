# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0012_auto_20141127_0720'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='giftcertificate',
            options={'ordering': ['purchased_for']},
        ),
        migrations.AddField(
            model_name='healer',
            name='booking_healersource_fee',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'1% of all online bookings'), (2, b'$15 / month flat rate')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='healer',
            name='booking_payment_requirement',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'Require full amount on booking'), (2, b"Require client to enter credit card, but don't charge anything"), (3, b'Clients can book without credit card')]),
        ),
    ]
