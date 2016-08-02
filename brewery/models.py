from django.contrib.auth.models import Group

from django.db import models

from datetime import datetime

import uuid

class BrewingCompany(models.Model):
    group = models.OneToOneField(Group,null=True)

    @property
    def name(self): return self.group.name

    def __unicode__(self):
        return u"{}".format(self.group.name)

class Brewery(models.Model):
    name = models.CharField(max_length=256)
    address1 = models.CharField(max_length=256,null=True,blank=True)
    address2 = models.CharField(max_length=256,null=True,blank=True)
    city = models.CharField(max_length=256,null=True,blank=True)
    state = models.CharField(max_length=256,null=True,blank=True)
    country = models.CharField(max_length=256,null=True,blank=True)
    
    company = models.ForeignKey(BrewingCompany,null=True)
    
    def __unicode__(self):
        return u"{}".format(self.name)

class Brewhouse(models.Model):
    name = models.CharField(max_length=64)
    brewery = models.ForeignKey(Brewery,null=True)
    
    key = models.UUIDField(default=uuid.uuid4)
    secret = models.UUIDField(default=uuid.uuid4)
    
    @property
    def active(self):
        return self.recipeinstance_set.filter(active=True).count() > 0
    
    def __unicode__(self):
        return u"{} - {}".format(self.name,self.brewery)

class BeerStyle(models.Model):
    name = models.CharField(max_length=128,unique=True)
    
    def __unicode__(self):
        return u"{}".format(self.name)

class Recipe(models.Model):
    name = models.CharField(max_length=64)
    style = models.ForeignKey(BeerStyle,null=True)
    
    def __unicode__(self):
        return u"{}({})".format(self.name,self.style.name)

class RecipeInstance(models.Model):
    recipe = models.ForeignKey(Recipe)
    date = models.DateField(default=datetime.now)
    brewhouse = models.ForeignKey(Brewhouse,null=True)
    active = models.BooleanField(default=False)
    
    def __unicode__(self):
        return u"{} - {} ({}){}".format(self.recipe.name,self.date,self.brewhouse.name,u"ACTIVE" if self.active else u"")

class AssetSensor(models.Model):
    name=models.CharField(max_length=64)
    brewery = models.ForeignKey(Brewhouse,null=True)
    
    def __unicode__(self):
        return u"{}-{}".format(unicode(self.brewery),self.name)
    
    
class TimeSeriesDataPoint(models.Model):
    sensor = models.ForeignKey(AssetSensor)
    recipe_instance = models.ForeignKey(RecipeInstance)
    
    time = models.DateTimeField()
    value = models.FloatField()