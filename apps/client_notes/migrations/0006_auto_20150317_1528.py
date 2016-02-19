# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_initial_order(apps, schema_editor):
    Diagram = apps.get_model('client_notes', 'Diagram')
    for diagram in Diagram.objects.all():
        diagram.order = diagram.pk * 10
        diagram.save()

class Migration(migrations.Migration):

    dependencies = [
        ('client_notes', '0005_diagram_order'),
    ]

    operations = [
	migrations.RunPython(set_initial_order)
    ]
