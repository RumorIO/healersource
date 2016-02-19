# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('modality', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('healers', '0002_auto_20141107_1933'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealingRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remote_healing', models.BooleanField(default=False)),
                ('trade_for_services', models.BooleanField(default=False)),
                ('cost_per_session', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('show_full_name', models.BooleanField(default=False)),
                ('show_photo', models.BooleanField(default=False)),
                ('status', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, b'DELETED')])),
                ('location', models.ForeignKey(blank=True, to='healers.Zipcode', null=True)),
                ('specialities', models.ManyToManyField(to='modality.Modality')),
                ('speciality_categories', models.ManyToManyField(to='modality.ModalityCategory')),
                ('user', models.ForeignKey(related_name=b'healing_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HealingRequestSearch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remote_healing', models.BooleanField(default=False)),
                ('trade_for_services', models.BooleanField(default=False)),
                ('cost_per_session', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('near_my_location', models.BooleanField(default=False)),
                ('only_my_specialities', models.BooleanField(default=False)),
                ('saved', models.BooleanField(default=False)),
                ('location', models.ForeignKey(blank=True, to='healers.Zipcode', null=True)),
                ('specialities', models.ManyToManyField(to='modality.Modality')),
                ('speciality_categories', models.ManyToManyField(to='modality.ModalityCategory')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
