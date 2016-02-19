# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_auto_20141107_1933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='link_source',
            field=models.CharField(default=b'', max_length=32, null=True, blank=True, choices=[(b'facebook', b'Facebook'), (b'twitter', b'Instagram'), (b'twitter', b'Twitter'), (b'linkedin', b'LinkedIn'), (b'google', b'Google Search'), (b'google', b'A Friend'), (b'google', b'Found a Flyer'), (b'google', b'Other')]),
#            preserve_default=True,
        ),
    ]
