# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('healers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(related_name=b'intake_form_answers', to='clients.Client')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnswerResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', encrypted_fields.fields.EncryptedTextField()),
                ('answer', models.ForeignKey(related_name=b'results', to='intake_forms.Answer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IntakeForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer_option', models.PositiveSmallIntegerField(default=0, choices=[(2, b'Send intake form to client by email (this will send the client an email containing all questions, and they will email their responses to you)'), (1, b"Client fills out intake form on HealerSource, and the responses are sent to me in an email. This will not store any of the client's information on HealerSource"), (0, b'Store Intake form in HealerSource')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('healer', models.ForeignKey(related_name=b'intake_forms', to='healers.Healer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IntakeFormSentHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(related_name=b'intake_form_sent_history_client', to='clients.Client')),
                ('healer', models.ForeignKey(related_name=b'intake_form_sent_history_healer', to='healers.Healer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField()),
                ('answer_rows', models.PositiveSmallIntegerField(default=1, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)])),
                ('form', models.ForeignKey(related_name=b'questions', to='intake_forms.IntakeForm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='answerresult',
            name='question',
            field=models.ForeignKey(related_name=b'results', to='intake_forms.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='form',
            field=models.ForeignKey(to='intake_forms.IntakeForm'),
            preserve_default=True,
        ),
    ]
