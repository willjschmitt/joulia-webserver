from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import Group,User
from .models import Brewhouse, Brewery, BrewingCompany
from .models import BeerStyle, Recipe
from .views import launch_recipe_instance, end_recipe_instance

from django.test import Client

import json

class RecipeInstanceTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("john","john@example.com","smith")
        group = Group.objects.create(name="Joulia Brewing Company")
        group.user_set.add(user)
        
        self.c = Client()
        self.c.post('/login/', {'username': 'john', 'password': 'smith'})
        
        self.brewing_company = BrewingCompany.objects.create(group=group)
        self.brewery = Brewery.objects.create(name="Main Facility",company=self.brewing_company)
        self.brewhouse = Brewhouse.objects.create(name="Brewhouse 1 (1/6 BBL)",brewery=self.brewery)
        
        style = BeerStyle.objects.create(name="American IPA")
        self.recipe = Recipe.objects.create(name="Schmittfaced",style=style)
    
    def test_start_stop_instance(self):
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data))
        self.assertEqual(response.status_code, 200)
        recipe_instance = response.json()['recipe_instance']
         
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, 200)