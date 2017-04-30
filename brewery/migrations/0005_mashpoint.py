# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-30 02:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0004_auto_20170423_1917'),
    ]

    operations = [
        migrations.CreateModel(
            name='MashPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField()),
                ('time', models.FloatField(default=0.0)),
                ('temperature', models.FloatField(default=0.0)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='brewery.Recipe')),
            ],
        ),
    ]
