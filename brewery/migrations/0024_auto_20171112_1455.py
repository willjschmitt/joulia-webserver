# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-12 22:55
from __future__ import unicode_literals

from django.db import migrations
from brewery import permissions


def add_continuous_integration_group(apps, _):
    """Adds continuous_integration group for releasing new software versions
    that depend on joulia-webserver for releasing updates.
    """
    Group = apps.get_model('auth', 'Group')
    Group.objects.create(name=permissions.CONTINUOUS_INTEGRATION_GROUP_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0023_auto_20171001_1623'),
    ]

    operations = [
        migrations.RunPython(add_continuous_integration_group)
    ]