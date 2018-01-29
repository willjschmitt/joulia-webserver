# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from brewery.migrations.utils.bjcp_guidelines import add_styles


class Migration(migrations.Migration):
    dependencies = [
        ('brewery', '0037_auto_20180128_1405'),
    ]

    operations = [
        migrations.RunPython(add_styles)
    ]
