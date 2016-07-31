from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import Group,User
from . import models
from .views import launch_recipe_instance, end_recipe_instance

from django.test import Client

import json

from rest_framework import status

class BreweryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.c = Client()
        
        user = User.objects.create_user("john","john@example.com","smith")
        group = Group.objects.create(name="Joulia Brewing Company")
        group.user_set.add(user)
        
        User.objects.create_user("alex","alex@example.com","notamember")
        
        cls.brewing_company = models.BrewingCompany.objects.create(group=group)
        cls.brewery = models.Brewery.objects.create(name="Main Facility",company=cls.brewing_company)
        cls.brewhouse = models.Brewhouse.objects.create(name="Brewhouse 1 (1/6 BBL)",brewery=cls.brewery)
        
        style = models.BeerStyle.objects.create(name="American IPA")
        cls.recipe = models.Recipe.objects.create(name="Schmittfaced",style=style)
        
    def login_as_normal_user(self):
        self.c.post('/login/', {'username': 'john', 'password': 'smith'})
        
    def login_as_alternate_user(self):
        self.c.post('/login/', {'username': 'alex', 'password': 'notamember'})
        
        
class TimeSeriesIdentifyTestCase(BreweryTestCase):
    def test_existing_sensor(self):
        self.login_as_normal_user()
        
        sensor = models.AssetSensor.objects.create(name="existing_sensor",brewery=self.brewhouse)
        recipe_instance = models.RecipeInstance.objects.create(recipe=self.recipe,
                                                               brewhouse=self.brewhouse,
                                                               active=True)
        
        data = {'recipe_instance':recipe_instance.pk,
                'name':"existing_sensor"}
        response = self.c.post('/live/timeseries/identify/',
                               content_type="application/json",
                               data=json.dumps(data))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['sensor'],sensor.pk)
        
    def test_nonexisting_sensor(self):
        self.login_as_normal_user()
        pre_sensorcount = models.AssetSensor.objects.count()
        recipe_instance = models.RecipeInstance.objects.create(recipe=self.recipe,
                                                               brewhouse=self.brewhouse,
                                                               active=True)
        
        data = {'recipe_instance':recipe_instance.pk,
                'name':"nonexisting_sensor"}
        response = self.c.post('/live/timeseries/identify/',
                               content_type="application/json",
                               data=json.dumps(data))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        post_sensorcount = models.AssetSensor.objects.count()
        
        self.assertEqual(post_sensorcount,pre_sensorcount+1)

class RecipeInstanceLaunchTestCase(BreweryTestCase):
    def test_launch_instance_success(self):
        self.login_as_normal_user()
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data),follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_launch_instance_already_active(self):
        self.login_as_normal_user()
        models.RecipeInstance.objects.create(recipe=self.recipe,
                                             brewhouse=self.brewhouse,
                                             active=True)
        
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_launch_instance_no_permission(self):
        self.login_as_alternate_user()
        models.RecipeInstance.objects.create(recipe=self.recipe,
                                             brewhouse=self.brewhouse)
        
        #start an instance
        launch_data = {'recipe':self.recipe.pk,
                       'brewhouse':self.brewhouse.pk}
        response = self.c.post('/brewery/brewhouse/launch',
                               content_type="application/json",
                               data=json.dumps(launch_data))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
class RecipeInstanceEndTestCase(BreweryTestCase):
    def test_end_instance_success(self):
        self.login_as_normal_user()
        recipe_instance = models.RecipeInstance.objects.create(recipe=self.recipe,
                                                               brewhouse=self.brewhouse,
                                                               active=True)
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance.pk}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_end_instance_already_active(self):
        self.login_as_normal_user()
        recipe_instance = models.RecipeInstance.objects.create(recipe=self.recipe,
                                                               brewhouse=self.brewhouse,
                                                               active=False)
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance.pk}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_end_instance_no_permission(self):
        self.login_as_alternate_user()
        recipe_instance = models.RecipeInstance.objects.create(recipe=self.recipe,
                                                               brewhouse=self.brewhouse)
        
        #end the instance
        end_data = {'recipe_instance':recipe_instance.pk}
        response = self.c.post('/brewery/brewhouse/end',
                               content_type="application/json",
                               data=json.dumps(end_data))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)