# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('review', models.TextField()),
                ('rating', models.PositiveSmallIntegerField(default=5, choices=[(5, b'5 Stars'), (4, b'4 Stars'), (3, b'3 Stars'), (2, b'2 Stars'), (1, b'1 Star')])),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('reply', models.TextField(blank=True)),
                ('reply_date', models.DateTimeField(null=True, blank=True)),
                ('reply_visible', models.BooleanField(default=False)),
                ('healer', models.ForeignKey(related_name=b'reviews', to='healers.Healer')),
                ('reviewer', models.ForeignKey(to='clients.Client')),
            ],
            options={
                'ordering': ['-date'],
            },
            bases=(models.Model,),
        ),
    ]
