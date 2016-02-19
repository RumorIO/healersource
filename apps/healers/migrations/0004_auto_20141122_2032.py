# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0003_healer_remote_sessions'),
    ]

    operations = [
        migrations.CreateModel(
            name='WellnessCenterGoogleEventId',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('google_event_id', models.CharField(max_length=1024, blank=True)),
                ('appointment', models.ForeignKey(related_name=b'wellness_center_google_event_ids', to='healers.Appointment')),
                ('wellness_center', models.ForeignKey(to='healers.WellnessCenter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='wellnesscentergoogleeventlink',
            name='appointment',
        ),
        migrations.RemoveField(
            model_name='wellnesscentergoogleeventlink',
            name='wellness_center',
        ),
        migrations.DeleteModel(
            name='WellnessCenterGoogleEventLink',
        ),
        migrations.RenameField(
            model_name='appointment',
            old_name='google_event_link',
            new_name='google_event_id',
        ),
        migrations.RenameField(
            model_name='healer',
            old_name='google_calendar_edit_link',
            new_name='google_calendar_id',
        ),
        migrations.RemoveField(
            model_name='healer',
            name='google_calendar_feed_link',
        ),
    ]
