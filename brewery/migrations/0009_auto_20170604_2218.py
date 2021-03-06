# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-05 05:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0008_auto_20170522_1850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brewhouse',
            name='token',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='authtoken.Token'),
        ),
        migrations.AlterField(
            model_name='brewhouse',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
