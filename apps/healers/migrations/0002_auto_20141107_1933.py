# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0002_auto_20141107_1933'),
        ('sync_hs', '0001_initial'),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='unavailableslot',
            name='calendar',
            field=models.ForeignKey(blank=True, to='sync_hs.UnavailableCalendar', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='unavailableslot',
            name='healer',
            field=models.ForeignKey(to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='treatmenttypelength',
            name='treatment_type',
            field=models.ForeignKey(related_name=b'lengths', to='healers.TreatmentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='treatmenttype',
            name='healer',
            field=models.ForeignKey(related_name=b'healer_treatment_types', to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='treatmenttype',
            name='rooms',
            field=models.ManyToManyField(related_name=b'treatment_types', null=True, to='healers.Room', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='room',
            name='location',
            field=models.ForeignKey(related_name=b'rooms', to='healers.Location'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='healertimeslot',
            name='healer',
            field=models.ForeignKey(to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='healertimeslot',
            name='location',
            field=models.ForeignKey(default=None, to='healers.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='healer',
            name='wellness_center_permissions',
            field=models.ManyToManyField(to='healers.WellnessCenter', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='discountcode',
            name='healer',
            field=models.ForeignKey(related_name=b'discount_codes', to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='base_appointment',
            field=models.ForeignKey(default=None, to='healers.Appointment', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='client',
            field=models.ForeignKey(to='clients.Client'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='created_by',
            field=models.ForeignKey(related_name=b'created_appts', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='discount_code',
            field=models.ForeignKey(blank=True, to='healers.DiscountCode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='healer',
            field=models.ForeignKey(related_name=b'healer_appointments', to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='last_modified_by',
            field=models.ForeignKey(related_name=b'modified_appts', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='location',
            field=models.ForeignKey(default=None, to='healers.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='room',
            field=models.ForeignKey(default=None, to='healers.Room', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='appointment',
            name='treatment_length',
            field=models.ForeignKey(default=None, to='healers.TreatmentTypeLength', null=True),
            preserve_default=True,
        ),
    ]
