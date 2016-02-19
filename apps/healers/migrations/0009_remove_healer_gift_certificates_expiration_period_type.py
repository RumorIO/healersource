# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0008_auto_20141124_0527'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='healer',
            name='gift_certificates_expiration_period_type',
        ),
    ]
