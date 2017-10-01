# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-10-01 23:23
from __future__ import unicode_literals

from django.db import migrations
import logging


LOGGER = logging.getLogger(__name__)


def add_malt_ingredients(apps, _):
    """Adds malt ingredients from malt_ingredients.tsv into the MaltIngredient
    database. If an ingredient already exists with the provided name, it will
    skip it.
    """
    MaltIngredient = apps.get_model('brewery', 'MaltIngredient')
    with open('brewery/migrations/malt_ingredients.tsv') as ingredient_file:
        for row in ingredient_file:
            try:
                if row[0] == '#':
                    LOGGER.info(row)
                    continue
                name, _, _, color_string, _, sg_string, _ = row.split('\t')
                if MaltIngredient.objects.filter(name=name).exists():
                    LOGGER.warning('%s already exists in database. Skipping.',
                                   name)
                    continue
                color = float(color_string.replace('SRM', '').strip())
                sg = float(sg_string.replace('SG', '').strip())
                MaltIngredient.objects.create(
                    name=name, color=color, potential_sg_contribution=sg)
            except Exception as e:
                raise Exception("In " + row + ": " + e.args[0])


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0022_auto_20170925_1342'),
    ]

    operations = [
        migrations.RunPython(add_malt_ingredients)
    ]