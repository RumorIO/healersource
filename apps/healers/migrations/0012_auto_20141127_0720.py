# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0011_auto_20141124_1201'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='giftcertificate',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='giftcertificate',
            name='code',
        ),
        migrations.RemoveField(
            model_name='giftcertificate',
            name='healer',
        ),
        migrations.AddField(
            model_name='discountcode',
            name='is_gift_certificate',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='discountcode',
            name='remaining_uses',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='giftcertificate',
            name='discount_code',
            field=models.ForeignKey(default='1', to='healers.DiscountCode'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='giftcertificate',
            name='message',
            field=models.TextField(default=b'', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
