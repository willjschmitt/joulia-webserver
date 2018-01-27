# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import logging


LOGGER = logging.getLogger(__name__)


def add_yeast_ingredients_wyeast(apps, _):
    """Adds malt ingredients from malt_ingredients.tsv into the MaltIngredient
    database. If an ingredient already exists with the provided name, it will
    skip it.
    """
    YeastIngredient = apps.get_model('brewery', 'YeastIngredient')
    with open('brewery/migrations/yeast_ingredients_wyeast.tsv') as ingredient_file:
        for row in ingredient_file:
            try:
                if row[0] == '#':
                    LOGGER.info(row)
                    continue
                name, low_attenuation_pct_str, high_attentuation_pct_str, \
                    low_temperature_str, high_temperature_str, abv_pct_str \
                    = row.split('\t')
                if YeastIngredient.objects.filter(name=name).exists():
                    LOGGER.warning('%s already exists in database. Skipping.',
                                   name)
                    continue

                low_attenuation_pct = float(low_attenuation_pct_str)
                high_attenuation_pct = float(high_attentuation_pct_str)
                low_temperature = float(low_temperature_str)
                high_temperature = float(high_temperature_str)
                abv_pct = float(abv_pct_str)

                low_attenuation = low_attenuation_pct / 100.0
                high_attenuation = high_attenuation_pct / 100.0
                abv_tolerance = abv_pct / 100.0

                YeastIngredient.objects.create(
                    name=name, low_attenuation=low_attenuation,
                    high_attenuation=high_attenuation,
                    low_temperature=low_temperature,
                    high_temperature=high_temperature,
                    abv_tolerance=abv_tolerance)
            except Exception as e:
                raise Exception("In " + row + ": " + e.args[0])


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0031_auto_20180127_1355'),
    ]

    operations = [
        migrations.RunPython(add_yeast_ingredients_wyeast)
    ]
