# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-09-19 15:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dengue_linebot', '0035_auto_20170622_1308'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportZapperMsg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_time', models.DateTimeField()),
                ('content', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='lineuser',
            name='zapper_id',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='botreplylog',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bot_reply_log', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='govreport',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gov_faculty', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='messagelog',
            name='speaker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_log', to='dengue_linebot.LineUser'),
        ),
        migrations.AlterField(
            model_name='suggestion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suggestion', to='dengue_linebot.LineUser'),
        ),
        migrations.AddField(
            model_name='reportzappermsg',
            name='reporter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_zapper_msg', to='dengue_linebot.LineUser'),
        ),
    ]