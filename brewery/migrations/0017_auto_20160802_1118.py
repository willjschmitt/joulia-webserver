# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-02 15:18
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0016_auto_20160724_1627'),
    ]

    operations = [
        migrations.AddField(
            model_name='brewhouse',
            name='key',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AddField(
            model_name='brewhouse',
            name='secret',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]
