# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-24 20:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0015_auto_20160721_2125'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipeinstance',
            old_name='brewery',
            new_name='brewhouse',
        ),
    ]