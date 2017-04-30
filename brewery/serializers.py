"""Django rest framework serializers for the brewery app.
"""
from rest_framework import serializers

from brewery import models


class BrewingCompanySerializer(serializers.ModelSerializer):
    """Standard serializer for BrewingCompany model."""
    class Meta:
        model = models.BrewingCompany
        fields = ('id', 'group', 'name',)


class BrewerySerializer(serializers.ModelSerializer):
    """Standard serializer for Brewery."""
    class Meta:
        model = models.Brewery
        fields = '__all__'


class BrewhouseSerializer(serializers.ModelSerializer):
    """Standard serializer for Brewhouse."""
    active = serializers.ReadOnlyField()

    class Meta:
        model = models.Brewhouse
        fields = '__all__'


class BeerStyleSerializer(serializers.ModelSerializer):
    """Standard serializer for BeerStyle."""
    class Meta:
        model = models.BeerStyle
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Standard serializer for Recipe."""
    last_brewed = serializers.SerializerMethodField()
    number_of_batches = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'style', 'last_brewed', 'number_of_batches',)

    @staticmethod
    def get_last_brewed(recipe):
        recipe_instances = recipe.recipeinstance_set
        if recipe_instances.count() != 0:
            return recipe_instances.latest('date').date
        else:
            return None

    @staticmethod
    def get_number_of_batches(recipe):
        return recipe.recipeinstance_set.count()


class MashPointSerializer(serializers.ModelSerializer):
    """Standard serializer for MashPoint."""
    index = serializers.IntegerField(required=False)

    class Meta:
        model = models.MashPoint
        fields = '__all__'


class RecipeInstanceSerializer(serializers.ModelSerializer):
    """Standard serializer for RecipeInstance."""
    class Meta:
        model = models.RecipeInstance
        fields = '__all__'


class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    """Standard serializer for TimeSeriesDataPoint."""
    class Meta:
        model = models.TimeSeriesDataPoint
        fields = '__all__'
