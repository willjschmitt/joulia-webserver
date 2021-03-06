# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-27 23:36
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0032_yeast_ingredients_wyeast'),
    ]

    operations = [
        migrations.RenameField(
            model_name='yeastingredient',
            old_name='abv_tolerance',
            new_name='high_abv_tolerance',
        ),
        migrations.AddField(
            model_name='yeastingredient',
            name='low_abv_tolerance',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]),
        ),
    ]
