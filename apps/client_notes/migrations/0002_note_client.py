# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('client_notes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='client',
            field=models.ForeignKey(to='clients.Client'),
            preserve_default=True,
        ),
    ]
