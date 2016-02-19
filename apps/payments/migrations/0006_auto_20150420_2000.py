# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentevent',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='paymenteventprocessingexception',
            name='event',
        ),
        migrations.DeleteModel(
            name='PaymentEvent',
        ),
        migrations.DeleteModel(
            name='PaymentEventProcessingException',
        ),
    ]
