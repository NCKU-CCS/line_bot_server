# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-09-05 09:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LINEUser',
            fields=[
                ('user_mid', models.TextField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('picture_url', models.TextField()),
                ('status_message', models.TextField()),
            ],
        ),
    ]
