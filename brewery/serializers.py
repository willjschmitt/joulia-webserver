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
    last_brewed = serializers.SerializerMethodField()
    number_of_batches = serializers.SerializerMethodField()
    class Meta:
        model = Recipe
        fields = ('name', 'style','last_brewed','number_of_batches',)
        
    def get_last_brewed(self, obj):
        recipe_instances = obj.recipeinstance_set
        if recipe_instances.count()!=0:
            return recipe_instances.latest('date').date
        else:
            return None
        
    def get_number_of_batches(self,obj):
        return obj.recipeinstance_set.count()

class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSeriesDataPoint