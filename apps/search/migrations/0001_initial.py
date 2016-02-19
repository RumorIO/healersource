# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('modality', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealerSearchHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modality', models.ForeignKey(blank=True, to='modality.Modality', null=True)),
                ('modality_category', models.ForeignKey(blank=True, to='modality.ModalityCategory', null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('zipcode', models.ForeignKey(blank=True, to='healers.Zipcode', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
