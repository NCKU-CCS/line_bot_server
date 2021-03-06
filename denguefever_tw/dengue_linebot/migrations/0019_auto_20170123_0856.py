# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-23 08:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dengue_linebot', '0018_auto_20161213_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botreplylog',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bot_reply_log', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='govreport',
            name='lat',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='govreport',
            name='lng',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='govreport',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gov_faculty', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='speaker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_log', to='dengue_linebot.LineUser'),
        ),
    ]
