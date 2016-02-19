# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        ('clients', '0002_auto_20141107_1933'),
        ('contenttypes', '0001_initial'),
        ('healers', '0002_auto_20141107_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventlocationdate',
            name='location',
            field=models.ForeignKey(to='healers.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventattendee',
            name='person_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='attendees',
            field=models.ManyToManyField(to='events.EventAttendee'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='client',
            field=models.ForeignKey(related_name=b'events', to='clients.Client'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='hosts',
            field=models.ManyToManyField(to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='location_dates',
            field=models.ManyToManyField(to='events.EventLocationDate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='type',
            field=models.ForeignKey(to='events.EventType'),
            preserve_default=True,
        ),
    ]
