# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ambassador', '0001_initial'),
        ('clients', '0004_auto_20150205_1307'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='ambassador',
            field=models.ForeignKey(blank=True, to='clients.Client', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='ambassador_plan',
            field=models.ForeignKey(blank=True, to='ambassador.Plan', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='ambassador_homepage',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='client',
            name='link_source',
            field=models.CharField(default=b'', max_length=32, null=True, blank=True, choices=[(b'facebook', b'Facebook'), (b'twitter', b'Instagram'), (b'twitter', b'Twitter'), (b'linkedin', b'LinkedIn'), (b'google', b'Google Search'), (b'friend', b'A Friend'), (b'flyer', b'Found a Flyer'), (b'other', b'Other')]),
            preserve_default=True,
        ),
    ]
