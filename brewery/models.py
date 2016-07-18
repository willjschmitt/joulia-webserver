from django.contrib.auth.models import Group

from django.db import models

from datetime import datetime

class BrewingCompany(models.Model):
    group = models.OneToOneField(Group,null=True)

# Create your models here.
class Brewery(models.Model):
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=64)
    
    company = models.ForeignKey(BrewingCompany,null=True)
    
    @property
    def active(self):
        return self.recipeinstance_set.filter(active=True).count() > 0

class BeerStyle(models.Model):
    name = models.CharField(max_length=128,unique=True)

class Recipe(models.Model):
    name = models.CharField(max_length=64)
    style = models.ForeignKey(BeerStyle,null=True)
    

class RecipeInstance(models.Model):
    recipe = models.ForeignKey(Recipe)
    date = models.DateField(default=datetime.now)
    brewery = models.ForeignKey(Brewery,null=True)
    active = models.BooleanField(default=False)

class Asset(models.Model):
    name=models.CharField(max_length=64)
    
    def __unicode__(self):
        return u"{}".format(self.name)

class AssetSensor(models.Model):
    name=models.CharField(max_length=64)
    asset = models.ForeignKey(Asset)
    
    def __unicode__(self):
        return u"{}-{}".format(unicode(self.asset),self.name)
    
    
class TimeSeriesDataPoint(models.Model):
    sensor = models.ForeignKey(AssetSensor)
    recipe_instance = models.ForeignKey(RecipeInstance)
    
    time = models.DateTimeField()
    value = models.FloatField()