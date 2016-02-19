# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Diagram',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code_name', models.CharField(unique=True, max_length=50)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Dot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position_x', models.PositiveSmallIntegerField()),
                ('position_y', models.PositiveSmallIntegerField()),
                ('text', models.CharField(default=b'', max_length=1024)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FavoriteDiagram',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Marker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('color', models.CharField(max_length=7, null=True, blank=True)),
                ('image', models.CharField(max_length=50, null=True, blank=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('finalized_date', models.DateTimeField(null=True, blank=True)),
                ('subjective', models.CharField(default=b'', max_length=250)),
                ('objective', models.CharField(default=b'', max_length=250)),
                ('assessment', models.CharField(default=b'', max_length=250)),
                ('plan', models.CharField(default=b'', max_length=250)),
            ],
            options={
                'ordering': ['-pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('code_name', models.CharField(unique=True, max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
