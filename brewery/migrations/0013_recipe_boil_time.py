# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-20 01:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0012_auto_20170619_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='boil_time',
            field=models.FloatField(default=60.0),
        ),
    ]
