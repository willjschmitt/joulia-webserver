# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-21 01:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0010_brewingfacility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brewery',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='brewery.BrewingFacility'),
        ),
    ]