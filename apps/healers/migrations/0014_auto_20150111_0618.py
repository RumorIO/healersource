# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0014_auto_20150113_1415'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='healer',
            options={'verbose_name': 'healers', 'verbose_name_plural': 'healers', 'permissions': (('can_use_wcenter_schedule', 'Can use wellness center schedule'), ('can_use_notes', 'Can use notes'), ('can_use_booking_no_fee', 'Can use booking without fees'))},
        ),
        migrations.AddField(
            model_name='healer',
            name='intakeFormBooking',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'Prompt my clients to fill out my Intake Form online after booking'), (2, b'Send my clients an email with a link to my Intake Form after booking'), (3, b'No Intake Form on booking')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='healer',
            name='booking_healersource_fee',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'1% of online bookings'), (2, b'$15 / month flat rate')]),
        ),
    ]
