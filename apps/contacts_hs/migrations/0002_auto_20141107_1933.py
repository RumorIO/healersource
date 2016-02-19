# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts_hs', '0001_initial'),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactinfo',
            name='healer',
            field=models.ForeignKey(related_name=b'healer_contacts', to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactgroup',
            name='contacts',
            field=models.ManyToManyField(related_name=b'groups', to='contacts_hs.ContactInfo'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contactemail',
            name='contact',
            field=models.ForeignKey(related_name=b'emails', to='contacts_hs.ContactInfo'),
            preserve_default=True,
        ),
    ]
