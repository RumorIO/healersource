# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientlocation',
            name='location',
            field=models.ForeignKey(to='healers.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
