from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import Group,User
from .models import Brewhouse, Brewery, BrewingCompany
from .models import BeerStyle, Recipe, RecipeInstance
from .views import launch_recipe_instance, end_recipe_instance

from django.test import Client

import json

class BreweryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user("john","john@example.com","smith")
        group = Group.objects.create(name="Joulia Brewing Company")
        group.user_set.add(user)
        
        cls.c = Client()
        cls.c.post('/login/', {'username': 'john', 'password': 'smith'})
        
        cls.brewing_company = BrewingCompany.objects.create(group=group)
        cls.brewery = Brewery.objects.create(name="Main Facility",company=cls.brewing_company)
        cls.brewhouse = Brewhouse.objects.create(name="Brewhouse 1 (1/6 BBL)",brewery=cls.brewery)
        
        style = BeerStyle.objects.create(name="American IPA")
        cls.recipe = Recipe.objects.create(name="Schmittfaced",style=style)

class RecipeInstanceLaunchTestCase(BreweryTestCase):
    def test_launch_instance_success(self):
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data))
        self.assertEqual(response.status_code, 200)
        
    def test_launch_instance_already_active(self):
        RecipeInstance.objects.create(recipe=self.recipe,
                                      brewhouse=self.brewhouse,
                                      active=True)
        
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data))
        self.assertEqual(response.status_code, 400)
        
class RecipeInstanceEndTestCase(BreweryTestCase):
    def test_end_instance_success(self):
        recipe_instance = RecipeInstance.objects.create(recipe=self.recipe,
                                                        brewhouse=self.brewhouse,
                                                        active=True)
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance.pk}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, 200)
        
    def test_end_instance_already_active(self):
        recipe_instance = RecipeInstance.objects.create(recipe=self.recipe,
                                                        brewhouse=self.brewhouse,
                                                        active=False)
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance.pk}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, 400)