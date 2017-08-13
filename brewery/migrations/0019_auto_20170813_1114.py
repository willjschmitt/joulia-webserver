# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-13 18:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0018_auto_20170812_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitteringingredientaddition',
            name='amount',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='maltingredientaddition',
            name='amount',
            field=models.FloatField(default=0.0),
        ),
    ]
