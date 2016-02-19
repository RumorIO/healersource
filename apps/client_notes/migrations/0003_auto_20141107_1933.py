# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client_notes', '0002_note_client'),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='healer',
            field=models.ForeignKey(related_name=b'notes', to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favoritediagram',
            name='diagrams',
            field=models.ManyToManyField(to='client_notes.Diagram', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='favoritediagram',
            name='healer',
            field=models.ForeignKey(to='healers.Healer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dot',
            name='diagram',
            field=models.ForeignKey(related_name=b'diagrams', to='client_notes.Diagram'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dot',
            name='marker',
            field=models.ForeignKey(related_name=b'markers', to='client_notes.Marker'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dot',
            name='note',
            field=models.ForeignKey(related_name=b'dots', to='client_notes.Note'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='diagram',
            name='section',
            field=models.ForeignKey(to='client_notes.Section'),
            preserve_default=True,
        ),
    ]
