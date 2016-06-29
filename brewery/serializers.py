'''
Created on Jun 20, 2016

@author: Will
'''
from rest_framework import serializers

from .models import TimeSeriesDataPoint
from .models import Recipe
from .models import Brewery
from .models import BeerStyle

class BeerStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeerStyle

class BrewerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Brewery

class RecipeSerializer(serializers.ModelSerializer):
    style = serializers.SlugRelatedField(slug_field="name",queryset=BeerStyle.objects.all())
    class Meta:
        model = Recipe
        fields = ('name', 'style',)

class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSeriesDataPoint