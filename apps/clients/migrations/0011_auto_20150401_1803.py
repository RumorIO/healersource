# -*- coding: utf-8 -*-

from django.db import models, migrations


def convert_phonegap_app_signup(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    for client in Client.objects.filter(phonegap_signup=True):
        client.signup_source = 'app'
        client.save()


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0010_client_signup_source'),
    ]

    operations = [
        migrations.RunPython(convert_phonegap_app_signup),
    ]

