# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-28 22:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0036_hop_ingredients'),
    ]

    operations = [
        migrations.AddField(
            model_name='beerstyle',
            name='high_abv',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='high_final_gravity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='high_ibu',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='high_original_gravity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='high_srm',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='low_abv',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='low_final_gravity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='low_ibu',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='low_original_gravity',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='low_srm',
            field=models.FloatField(default=0.0),
        ),
    ]
