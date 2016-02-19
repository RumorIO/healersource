# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0002_auto_20141107_1933'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GhpSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('send_to_ghp_members', models.BooleanField(default=False)),
                ('send_to_my_fb_friends', models.BooleanField(default=False)),
                ('send_to_my_favorites_only', models.BooleanField(default=False)),
                ('i_want_to_receive_healing', models.BooleanField(default=False)),
                ('user', models.OneToOneField(related_name=b'ghp_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HealingPersonStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_object_id', models.PositiveIntegerField()),
                ('status', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Normal'), (1, b'Favorite'), (2, b'To skip')])),
                ('client', models.ForeignKey(to='clients.Client')),
                ('person_content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=1024)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SentHealing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_object_id', models.PositiveIntegerField()),
                ('started_at', models.DateTimeField(null=True, blank=True)),
                ('ended_at', models.DateTimeField(null=True, blank=True)),
                ('duration', models.IntegerField(default=0)),
                ('skipped', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('person_content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('sent_by', models.ForeignKey(related_name=b'sent_healing', to='clients.Client')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
