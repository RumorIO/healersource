# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0014_auto_20150111_0618'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='healer',
            options={'verbose_name': 'healers', 'verbose_name_plural': 'healers', 'permissions': (('can_use_wcenter_schedule', 'Can use wellness center schedule'), ('can_use_notes', 'Can use notes'), ('can_use_booking_no_fee', 'Can use booking without fees'))},
        ),
        migrations.AddField(
            model_name='location',
            name='book_online_new',
            field=models.PositiveIntegerField(default=1, choices=[(1, b'Enable Online Bookings at this Location'), (0, b'Show Availability but Disable Online Bookings at this Location (Call to Book)'), (2, b'Hide This Location from Public View (only you can see it)')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='healer',
            name='booking_healersource_fee',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'1% of online bookings'), (2, b'$15 / month flat rate')]),
        ),
    ]
