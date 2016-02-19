# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from healers.models import Location

def transfer_book_online_data(apps, schema_editor):
    locations = Location.objects.all()
    for l in locations:
        if not l.book_online:
            l.book_online = False
            l.book_online_new = 0
            l.save()

class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0015_auto_20150114_0636'),
    ]

    operations = [
        migrations.RunPython(transfer_book_online_data)
    ]
