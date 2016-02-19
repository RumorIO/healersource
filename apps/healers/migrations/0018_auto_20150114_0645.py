# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('healers', '0017_remove_location_book_online'),
    ]

    operations = [
        migrations.RenameField(
            model_name='location',
            old_name='book_online_new',
            new_name='book_online',
        ),
    ]
