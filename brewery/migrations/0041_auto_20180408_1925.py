# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-04-09 02:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0040_recipe_brewhouse_efficiency'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timeseriesdatapoint',
            options={'get_latest_by': 'time'},
        ),
        migrations.AddField(
            model_name='recipe',
            name='post_boil_volume_gallons',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='recipe',
            name='pre_boil_volume_gallons',
            field=models.FloatField(default=0.0),
        ),
    ]