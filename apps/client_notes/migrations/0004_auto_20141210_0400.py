# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('client_notes', '0003_auto_20141107_1933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dot',
            name='text',
            field=encrypted_fields.fields.EncryptedCharField(default=b'', max_length=1024),
        ),
        migrations.AlterField(
            model_name='note',
            name='assessment',
            field=encrypted_fields.fields.EncryptedCharField(default=b'', max_length=1024),
        ),
        migrations.AlterField(
            model_name='note',
            name='objective',
            field=encrypted_fields.fields.EncryptedCharField(default=b'', max_length=1024),
        ),
        migrations.AlterField(
            model_name='note',
            name='plan',
            field=encrypted_fields.fields.EncryptedCharField(default=b'', max_length=1024),
        ),
        migrations.AlterField(
            model_name='note',
            name='subjective',
            field=encrypted_fields.fields.EncryptedCharField(default=b'', max_length=1024),
        ),
    ]
