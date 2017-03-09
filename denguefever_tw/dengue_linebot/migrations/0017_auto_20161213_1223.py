# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-13 12:23
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dengue_linebot', '0016_auto_20161208_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='GovReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.TextField()),
                ('note', models.TextField()),
                ('report_time', models.DateTimeField()),
                ('lng', models.FloatField()),
                ('lat', models.FloatField()),
                ('location', django.contrib.gis.db.models.fields.PointField(default='POINT(0.0 0.0)', geography=True, srid=4326)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gov_faculty', to='dengue_linebot.LineUser')),
            ],
        ),
        migrations.AlterField(
            model_name='botreplylog',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bot_reply_log', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='speaker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_log', to='dengue_linebot.LineUser'),
        ),
    ]