# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from brewery.migrations.utils.recipe_migrations import boil_volume_migrations


class Migration(migrations.Migration):
    dependencies = [
        ('brewery', '0041_auto_20180408_1925'),
    ]

    operations = [
        migrations.RunPython(boil_volume_migrations)
    ]
