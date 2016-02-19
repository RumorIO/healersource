# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarSyncQueueTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api', models.PositiveSmallIntegerField(choices=[(0, b'Google')])),
                ('status', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Waiting'), (1, b'Running'), (2, b'Fail')])),
                ('action', models.PositiveSmallIntegerField(choices=[(0, b'New'), (1, b'Update'), (2, b'Delete')])),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('appointment', models.ForeignKey(to='healers.Appointment')),
                ('wellness_center', models.ForeignKey(default=None, to='healers.WellnessCenter', null=True)),
            ],
            options={
                'ordering': ['id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CalendarSyncStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api', models.PositiveSmallIntegerField(choices=[(0, b'Google')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnavailableCalendar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api', models.PositiveSmallIntegerField(choices=[(0, b'Google')])),
                ('feed_link', models.CharField(max_length=1024)),
                ('title', models.CharField(max_length=1024, blank=True)),
                ('update_date', models.DateTimeField(null=True, blank=True)),
                ('healer', models.ForeignKey(to='healers.Healer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
