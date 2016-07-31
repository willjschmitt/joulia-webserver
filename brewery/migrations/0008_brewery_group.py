# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-18 01:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        ('brewery', '0007_auto_20160717_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='brewery',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.Group'),
        ),
    ]