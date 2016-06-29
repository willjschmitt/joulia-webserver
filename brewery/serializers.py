'''
Created on Jun 20, 2016

@author: Will
'''
from rest_framework import serializers

from .models import TimeSeriesDataPoint
from .models import Recipe
from .models import Brewery

class BrewerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Brewery

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe

class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSeriesDataPoint