# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approval_rating', models.PositiveIntegerField(default=0)),
                ('about', models.TextField(default=b'', verbose_name='about', blank=True)),
                ('referred_by', models.CharField(max_length=255, blank=True)),
                ('invite_message', models.TextField(default=b'', blank=True)),
                ('beta_tester', models.BooleanField(default=True)),
                ('send_reminders', models.BooleanField(default=True)),
                ('ghp_notification_frequency', models.CharField(default=b'every time', max_length=32, choices=[(b'every time', b'Every time I receive healing'), (b'daily', b'Once a day'), (b'weekly', b'Once a week'), (b'unsubscribe', b'Unsubscribe')])),
                ('website', models.CharField(default=b'', max_length=255, blank=True)),
                ('facebook', models.CharField(default=b'', max_length=255, blank=True)),
                ('twitter', models.CharField(default=b'', max_length=255, blank=True)),
                ('google_plus', models.CharField(default=b'', max_length=255, blank=True)),
                ('linkedin', models.CharField(default=b'', max_length=255, blank=True)),
                ('first_login', models.BooleanField(default=True)),
                ('date_modified', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('link_source', models.CharField(default=b'', max_length=32, null=True, blank=True, choices=[(b'facebook', b'Facebook'), (b'twitter', b'Twitter'), (b'linkedin', b'LinkedIn'), (b'google', b'Google Search'), (b'google', b'A Friend'), (b'google', b'Found a Flyer'), (b'google', b'Other')])),
            ],
            options={
                'verbose_name': 'client',
                'verbose_name_plural': 'clients',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClientLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client', models.ForeignKey(to='clients.Client')),
            ],
            options={
                'ordering': ['location'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClientPhoneNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'Mobile', max_length=42)),
                ('number', models.CharField(max_length=42)),
                ('client', models.ForeignKey(related_name=b'phone_numbers', to='clients.Client')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClientVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('title', models.CharField(max_length=255)),
                ('date_added', models.DateTimeField()),
                ('video_id', models.CharField(max_length=255)),
                ('videotype', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, b'Gallery Video'), (2, b'Client Video')])),
                ('client', models.ForeignKey(related_name=b'videos', to='clients.Client')),
            ],
            options={
                'ordering': ['-date_added'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.PositiveSmallIntegerField()),
                ('hidden', models.BooleanField(default=False)),
                ('client', models.ForeignKey(to='clients.Client')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'get_latest_by': 'id',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReferralsSent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client_email', models.EmailField(max_length=255, null=True)),
                ('type', models.PositiveSmallIntegerField(default=0, choices=[(0, b'Provider To Client'), (1, b'Client to Provider')])),
                ('message', models.TextField(default=None, null=True, blank=True)),
                ('date_sent', models.DateField(default=datetime.date.today)),
                ('client_user', models.ForeignKey(related_name=b'referral_client', to=settings.AUTH_USER_MODEL, null=True)),
                ('provider_user', models.ForeignKey(related_name=b'referral_provider', to=settings.AUTH_USER_MODEL)),
                ('referring_user', models.ForeignKey(related_name=b'referral_sender', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SiteJoinInvitation',
            fields=[
                ('joininvitation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='friends.JoinInvitation')),
                ('is_from_site', models.BooleanField(default=False)),
                ('is_to_healer', models.BooleanField(default=False)),
                ('create_friendship', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=('friends.joininvitation',),
        ),
        migrations.AlterUniqueTogether(
            name='referralssent',
            unique_together=set([('provider_user', 'client_user', 'referring_user')]),
        ),
    ]
