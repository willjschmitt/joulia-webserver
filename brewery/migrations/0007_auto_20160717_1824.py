# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-17 22:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0006_auto_20160629_2100'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HeatedVessel',
        ),
    ]
