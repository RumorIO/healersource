# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def create_plans(apps, schema_editor):
    Plan = apps.get_model("ambassador", "Plan")
    Level = apps.get_model("ambassador", "Level")

    # 9-month plan
    plan = Plan.objects.create(name='9-month')
    Level.objects.create(plan=plan, level=0, percent=0.5)
    Level.objects.create(plan=plan, level=1, percent=0.2)
    Level.objects.create(plan=plan, level=2, percent=0.1)

    # 18-month plan
    plan = Plan.objects.create(name='18-month')
    Level.objects.create(plan=plan, level=0, percent=0.25)
    Level.objects.create(plan=plan, level=1, percent=0.15)
    Level.objects.create(plan=plan, level=2, percent=0.05)

    # Lifetime plan
    plan = Plan.objects.create(name='Lifetime')
    Level.objects.create(plan=plan, level=0, percent=0.15)
    Level.objects.create(plan=plan, level=1, percent=0.05)
    Level.objects.create(plan=plan, level=2, percent=0.02)

class Migration(migrations.Migration):

    dependencies = [
        ('ambassador', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_plans)
    ]
