# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealerActions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=254, verbose_name=b'action', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HealerMails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, verbose_name=b'email id')),
                ('title', models.CharField(max_length=254, verbose_name=b'title')),
                ('body', models.TextField(verbose_name=b'body')),
                ('body_html', models.TextField(null=True, verbose_name=b'html', blank=True)),
                ('delay', models.PositiveIntegerField(verbose_name=b'delay in days')),
                ('once', models.BooleanField(default=False, db_index=True, verbose_name=b'send only once')),
                ('process', models.CharField(default=b'default', max_length=254, verbose_name=b'processor', db_index=True, choices=[(b'default', b'Default processor'), (b'welcome', b'Welcome mail processor'), (b'send_on_request', b'Send on request processor'), (b'ghp', b'Global Healing Project processor')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HealerSettings',
            fields=[
                ('key', models.SlugField(serialize=False, verbose_name=b'key', primary_key=True)),
                ('description', models.CharField(max_length=254, verbose_name=b'description')),
                ('value', models.TextField(verbose_name=b'value')),
                ('type', models.CharField(max_length=254, null=True, verbose_name=b'unused', blank=True)),
                ('web_only', models.BooleanField(default=True, db_index=True, verbose_name=b'can change only by web (here)')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='healeractions',
            unique_together=set([('action', 'content_type', 'object_id')]),
        ),
    ]
