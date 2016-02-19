# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_access', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAssociationDated',
            fields=[
                ('user_assoc', models.OneToOneField(primary_key=True, serialize=False, to='oauth_access.UserAssociation')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
