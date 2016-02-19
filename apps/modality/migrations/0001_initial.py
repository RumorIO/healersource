# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Modality',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', max_length=64, blank=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('visible', models.BooleanField(default=True, db_index=True)),
                ('approved', models.BooleanField(default=True, db_index=True)),
                ('rejected', models.BooleanField(default=False, db_index=True)),
                ('added_by', models.ForeignKey(related_name=b'added_modality', blank=True, to='healers.Healer', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModalityCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default=b'', max_length=64, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='modality',
            name='category',
            field=models.ManyToManyField(to='modality.ModalityCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modality',
            name='healer',
            field=models.ManyToManyField(to='healers.Healer'),
            preserve_default=True,
        ),
    ]
