# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from brewery.migrations.utils.hop_migrations import add_hop_ingredients


class Migration(migrations.Migration):
    dependencies = [
        ('brewery', '0035_copy_attenuations'),
    ]

    operations = [
        migrations.RunPython(add_hop_ingredients)
    ]
