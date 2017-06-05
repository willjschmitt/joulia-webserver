"""Tests for the brewery.views module.
"""

from django.contrib.auth.models import Group, User
from django.test import Client
from django.test import TestCase
import json
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import Mock

from brewery import models
from brewery import views


class BreweryTestBase(TestCase):
    """Tests for the Brewery REST views."""

    def setUp(self):
        self.c = Client()

        self.good_user = User.objects.create_user("john", "john@example.com",
                                                  "smith")
        group = Group.objects.create(name="Joulia Brewing Company")
        group.user_set.add(self.good_user)

        self.bad_user = User.objects.create_user("alex", "alex@example.com",
                                                 "notamember")

        self.brewing_company = models.BrewingCompany.objects.create(group=group)
        self.brewery = models.Brewery.objects.create(
            name="Main Facility", company=self.brewing_company)
        self.brewhouse = models.Brewhouse.objects.create(
            name="Brewhouse 1 (1/6 BBL)", brewery=self.brewery)

        style = models.BeerStyle.objects.create(name="American IPA")
        self.recipe = models.Recipe.objects.create(
            name="Schmittfaced", style=style, company=self.brewing_company)

    def login_as_normal_user(self):
        self.c.login(username='john', password='smith')

    def login_as_alternate_user(self):
        self.c.login(username='alex', password='notamember')


class BrewingCompanyApiMixinTest(BreweryTestBase):
    """Tests for BrewingCompanyApiMixin."""

    def test_get_queryset_correct_user(self):
        view = views.BrewingCompanyApiMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.brewing_company, got)

    def test_get_queryset_bad_user(self):
        view = views.BrewingCompanyApiMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.brewing_company, got)


class BreweryApiMixinTest(BreweryTestBase):
    """Tests for BreweryApiMixin."""

    def test_get_queryset_correct_user(self):
        view = views.BreweryApiMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.brewery, got)

    def test_get_queryset_bad_user(self):
        view = views.BreweryApiMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.brewery, got)


class BrewhouseApiMixinTest(BreweryTestBase):
    """Tests for BrewhouseApiMixin."""

    def test_get_queryset_correct_user(self):
        view = views.BrewhouseApiMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.brewhouse, got)

    def test_get_queryset_bad_user(self):
        view = views.BrewhouseApiMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.brewhouse, got)


class RecipeAPIMixinTest(BreweryTestBase):
    """Tests for RecipeAPIMixin."""

    def test_get_queryset_correct_user(self):
        view = views.RecipeAPIMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.recipe, got)

    def test_get_queryset_bad_user(self):
        view = views.RecipeAPIMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.recipe, got)


class MashPointAPIMixinTest(BreweryTestBase):
    """Tests for MashPointAPIMixin."""

    def setUp(self):
        super(MashPointAPIMixinTest, self).setUp()
        self.mash_point = models.MashPoint.objects.create(recipe=self.recipe)

    def test_get_queryset_correct_user(self):
        view = views.MashPointAPIMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.mash_point, got)

    def test_get_queryset_bad_user(self):
        view = views.MashPointAPIMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.mash_point, got)


class RecipeInstanceApiMixinTest(BreweryTestBase):
    """Tests for RecipeInstanceApiMixin."""

    def setUp(self):
        super(RecipeInstanceApiMixinTest, self).setUp()
        self.recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe)

    def test_get_queryset_correct_user(self):
        view = views.RecipeInstanceApiMixin()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.recipe_instance, got)

    def test_get_queryset_bad_user(self):
        view = views.RecipeInstanceApiMixin()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.recipe_instance, got)


class TimeSeriesNewHandlerTest(BreweryTestBase):
    """Tests for TimeSeriesNewHandler."""

    def setUp(self):
        super(TimeSeriesNewHandlerTest, self).setUp()
        sensor = models.AssetSensor.objects.create(brewhouse=self.brewhouse)
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe)
        self.data_point = models.TimeSeriesDataPoint.objects.create(
            sensor=sensor, recipe_instance=recipe_instance)

    def test_get_queryset_correct_user(self):
        view = views.TimeSeriesNewHandler()
        view.request = Mock(user=self.good_user)
        got = view.get_queryset()
        self.assertIn(self.data_point, got)

    def test_get_queryset_bad_user(self):
        view = views.TimeSeriesNewHandler()
        view.request = Mock(user=self.bad_user)
        got = view.get_queryset()
        self.assertNotIn(self.data_point, got)


class TimeSeriesIdentifyHandlerTest(BreweryTestBase):
    """Tests for TimeSeriesIdentifyHandler."""

    def test_existing_sensor(self):
        request = Mock(user=self.good_user)

        sensor = models.AssetSensor.objects.create(
            name="existing_sensor", brewhouse=self.brewhouse)
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=self.brewhouse, active=True)

        request.data = {'recipe_instance': recipe_instance.pk,
                        'name': "existing_sensor"}
        response = views.TimeSeriesIdentifyHandler.post(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['sensor'], sensor.pk)

    def test_nonexisting_sensor(self):
        request = Mock(user=self.good_user)
        pre_sensorcount = models.AssetSensor.objects.count()
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=self.brewhouse, active=True)

        request.data = {'recipe_instance': recipe_instance.pk,
                        'name': "nonexisting_sensor"}
        response = views.TimeSeriesIdentifyHandler.post(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_sensorcount = models.AssetSensor.objects.count()
        self.assertEqual(post_sensorcount, pre_sensorcount+1)

    def test_end_instance_no_permission(self):
        request = Mock(user=self.bad_user)
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=self.brewhouse, active=True)

        request.data = {'recipe_instance': recipe_instance.pk,
                        'name': "nonexisting_sensor"}
        response = views.TimeSeriesIdentifyHandler.post(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BrewhouseIdByTokenTest(TestCase):
    def test_no_token(self):
        user = User.objects.create()
        request = Mock(user=user)
        response = views.BrewhouseIdByToken.get(request)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_brewhouse(self):
        user = User.objects.create()
        Token.objects.create(user=user)
        request = Mock(user=user)
        response = views.BrewhouseIdByToken.get(request)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_token_correctly(self):
        group = Group.objects.create(name="A Brewing Company")
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company)
        brewhouse = models.Brewhouse.objects.create(brewery=brewery)
        request = Mock(user=brewhouse.token.user)
        response = views.BrewhouseIdByToken.get(request)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content.decode())['brewhouse'],
                          brewhouse.pk)
