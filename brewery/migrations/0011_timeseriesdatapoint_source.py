# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-19 13:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0010_auto_20170613_2055'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseriesdatapoint',
            name='source',
            field=models.TextField(max_length=4, null=True),
        ),
    ]
