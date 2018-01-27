# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_attenuations(apps, _):
    """Copies high_abv_tolerance to low_abv_tolerance.

    Does this for all ingredients where the first is set, but not the second.

    This is to complete migration 0033.
    """
    YeastIngredient = apps.get_model('brewery', 'YeastIngredient')
    for ingredient in YeastIngredient.objects.all():
        if (ingredient.low_abv_tolerance == 0.0
                and ingredient.high_abv_tolerance != 0.0):
            ingredient.low_abv_tolerance = ingredient.high_abv_tolerance
            ingredient.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brewery', '0034_yeast_ingredients_white_labs'),
    ]

    operations = [
        migrations.RunPython(copy_attenuations)
    ]
