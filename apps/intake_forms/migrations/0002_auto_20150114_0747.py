# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('intake_forms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_required',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='answerresult',
            name='text',
            field=encrypted_fields.fields.EncryptedTextField(blank=True),
        ),
    ]
