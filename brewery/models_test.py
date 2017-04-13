"""Tests for the brewery.models module.
"""

import datetime
from django.contrib.auth.models import Group
from django.test import TestCase

from brewery import models


class BrewingCompanyTest(TestCase):
    """Tests for the BrewingCompany model."""

    def test_name_with_group(self):
        group = Group.objects.create(name="Foo")
        brewing_company = models.BrewingCompany(group=group)

        self.assertEquals(brewing_company.name, "Foo")

    def test_name_without_group(self):
        brewing_company = models.BrewingCompany()
        self.assertEquals(brewing_company.name, None)

    def test_str(self):
        group = Group.objects.create(name="Foo")
        brewing_company = models.BrewingCompany.objects.create(group=group)

        self.assertEquals(str(brewing_company), "Foo")


class BreweryTest(TestCase):
    """Tests for the Brewery model"""

    def test_str(self):
        brewery = models.Brewery.objects.create(name="Foo")

        self.assertEquals(str(brewery), "Foo")


class BrewhouseTest(TestCase):
    """Test for the Brewhouse model."""

    def test_active_no_recipe_instances(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        self.assertFalse(brewhouse.active)

    def test_active_one_active_recipe_instance(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertTrue(brewhouse.active)

    def test_active_one_inactive_recipe_instance(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=False)
        self.assertFalse(brewhouse.active)

    def test_active_recipe_instance_one_active(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertEquals(brewhouse.active_recipe_instance, recipe_instance)

    def test_active_recipe_instance_one_inactive(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=False)
        self.assertIsNone(brewhouse.active_recipe_instance)

    def test_str(self):
        brewery = models.Brewery.objects.create(name="Foo")
        brewhouse = models.Brewhouse.objects.create(name="Bar", brewery=brewery)
        recipe = models.Recipe.objects.create(name="Baz")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertEquals(str(brewhouse), "Bar - Foo")


class BeerStyleTest(TestCase):
    """Tests for the BeerStyle model."""

    def test_str(self):
        beer_style = models.BeerStyle.objects.create(name="Foo")
        self.assertEquals(str(beer_style), "Foo")


class RecipeTest(TestCase):
    """Tests for the Recipe model."""

    def test_str(self):
        style = models.BeerStyle.objects.create(name="Bar")
        recipe = models.Recipe.objects.create(name="Foo", style=style)
        self.assertEquals(str(recipe), "Foo(Bar)")


class RecipeInstanceTest(TestCase):
    """Tests for the RecipeInstance model."""
    def setUp(self):
        self.recipe = models.Recipe.objects.create(name="Foo")

    def test_save_inactive_new_no_active(self):
        models.RecipeInstance.objects.create(recipe=self.recipe, active=False)

    def test_save_active_new_no_active(self):
        models.RecipeInstance.objects.create(recipe=self.recipe, active=True)

    def test_save_inactive_new_no_active_inactive_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)

    def test_save_active_new_no_active_inactive_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)

    def test_save_active_new_no_active_active_already_fails(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        with self.assertRaisesRegex(RuntimeError, "already active"):
            models.RecipeInstance.objects.create(
                recipe=self.recipe, brewhouse=brewhouse, active=True)

    def test_save_inactive_new_no_active_active_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)

    def test_save_active_self(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        recipe_instance.save()

    def test_str_active_without_brewhouse(self):
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe, active=True)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (None) ACTIVE")

    def test_str_active_with_brewhouse(self):
        brewhouse = models.Brewhouse.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe,
            brewhouse=brewhouse, active=True)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (Bar) ACTIVE")

    def test_str_inactive_without_brewhouse(self):
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe, active=False)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (None) INACTIVE")

    def test_str_inactive_with_brewhouse(self):
        brewhouse = models.Brewhouse.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe,
            brewhouse=brewhouse, active=False)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (Bar) INACTIVE")


class AssetSensorTest(TestCase):
    """Tests for the AssetSensor model."""

    def test_str(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        sensor = models.AssetSensor.objects.create(name="Bar",
                                                   brewhouse=brewhouse)
        self.assertEquals(str(sensor), "Foo-Bar")

    def test_str_no_brewhouse(self):
        sensor = models.AssetSensor.objects.create(name="Bar")
        self.assertEquals(str(sensor), "None-Bar")

class TimeSeriesDataPointTest(TestCase):
    """Tests for the TimeSeriesDataPoint model."""

    def test_str(self):
        sensor = models.AssetSensor.objects.create(name="Foo")
        datapoint = models.TimeSeriesDataPoint(
            sensor=sensor, value=1.0,
            time=datetime.datetime(2017, 4, 7, 21, 3, 59))
        self.assertEquals(str(datapoint), "Foo - 1.0 @ 2017-04-07 21:03:59")
