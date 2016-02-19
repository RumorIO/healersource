# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0020_auto_20150312_1903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discountcode',
            name='code',
            field=models.CharField(unique=True, max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='healer',
            name='booking_healersource_fee',
            field=models.PositiveSmallIntegerField(default=1, choices=[(2, b'$15 / month flat rate'), (1, b'1% of All Transactions')]),
            preserve_default=True,
        ),
    ]
