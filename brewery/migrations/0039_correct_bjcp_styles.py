# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from brewery.migrations.utils.bjcp_guidelines import add_styles


class Migration(migrations.Migration):
    dependencies = [
        ('brewery', '0038_update_bjcp_styles'),
    ]

    operations = [
        migrations.RunPython(add_styles)
    ]
