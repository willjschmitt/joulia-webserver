"""Unit tests for the brewery.serializers module."""

import datetime
from django.test import TestCase

from brewery import models
from brewery import serializers


class RecipeSerializerTest(TestCase):
    """Tests for the RecipeSerializer."""

    def test_get_last_brewed_no_instance(self):
        recipe = models.Recipe.objects.create(name="Foo")
        self.assertIsNone(serializers.RecipeSerializer.get_last_brewed(recipe))

    def test_get_last_brewed_one_instance(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        self.assertEquals(serializers.RecipeSerializer.get_last_brewed(recipe),
                          datetime.date(2017, 4, 7))

    def test_get_last_brewed_multiple_instances(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2016, 4, 7))
        self.assertEquals(serializers.RecipeSerializer.get_last_brewed(recipe),
                          datetime.date(2017, 4, 7))

    def test_get_number_of_batches(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2016, 4, 7))
        self.assertEquals(
            serializers.RecipeSerializer.get_number_of_batches(recipe), 2)
