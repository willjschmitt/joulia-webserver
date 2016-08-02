'''
Created on Jun 20, 2016

@author: Will
'''
from rest_framework import serializers

from . import models

class BrewingCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BrewingCompany
        fields = ('group','name',)

class BrewerySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Brewery

class BrewhouseSerializer(serializers.ModelSerializer):
    active = serializers.SerializerMethodField()
    class Meta:
        model = models.Brewhouse
        
    def get_active(self,obj):
        return obj.active

'''
Recipe Serializers
'''
class BeerStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BeerStyle
   
class RecipeSerializer(serializers.ModelSerializer):
    style = serializers.SlugRelatedField(slug_field="name",queryset=models.BeerStyle.objects.all())
    last_brewed = serializers.SerializerMethodField()
    number_of_batches = serializers.SerializerMethodField()
    class Meta:
        model = models.Recipe
        fields = ('id','name', 'style','last_brewed','number_of_batches',)
        
    def get_last_brewed(self, obj):
        recipe_instances = obj.recipeinstance_set
        if recipe_instances.count()!=0:
            return recipe_instances.latest('date').date
        else:
            return None
        
    def get_number_of_batches(self,obj):
        return obj.recipeinstance_set.count()
    
class RecipeInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RecipeInstance

class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TimeSeriesDataPoint