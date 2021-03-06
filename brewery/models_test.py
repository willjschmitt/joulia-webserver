"""Tests for the brewery.models module.
"""

import datetime
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test import TestCase
import kubernetes
from rest_framework.authtoken.models import Token
from unittest.mock import patch
import urllib3

from brewery import models


class BrewingCompanyTest(TestCase):
    """Tests for the BrewingCompany model."""

    def test_name_with_group(self):
        group = Group.objects.create(name="Foo")
        brewing_company = models.BrewingCompany(group=group)

        self.assertEquals(brewing_company.name, "Foo")

    def test_name_without_group(self):
        brewing_company = models.BrewingCompany()
        self.assertEquals(brewing_company.name, None)

    def test_str(self):
        group = Group.objects.create(name="Foo")
        brewing_company = models.BrewingCompany.objects.create(group=group)

        self.assertEquals(str(brewing_company), "Foo")


class BreweryTest(TestCase):
    """Tests for the Brewery model"""

    def test_str(self):
        brewery = models.Brewery.objects.create(name="Foo")

        self.assertEquals(str(brewery), "Foo")


class ResistanceTemperatureDeviceMeasurementTest(TestCase):
    """Tests for the ResistanceTemperatureDeviceMeasurement model."""

    def test_save_no_rtd(self):
        temperature_sensor = models.ResistanceTemperatureDeviceMeasurement()
        self.assertIsNone(temperature_sensor.rtd)
        temperature_sensor.save()
        self.assertIsNotNone(temperature_sensor.rtd)

    def test_save_has_rtd(self):
        temperature_sensor = models.ResistanceTemperatureDeviceMeasurement()
        rtd = models.ResistanceTemperatureDevice.objects.create()
        temperature_sensor.rtd = rtd
        temperature_sensor.save()
        self.assertIs(temperature_sensor.rtd, rtd)

    def test_save_no_amplifier(self):
        temperature_sensor = models.ResistanceTemperatureDeviceMeasurement()
        self.assertIsNone(temperature_sensor.amplifier)
        temperature_sensor.save()
        self.assertIsNotNone(temperature_sensor.amplifier)

    def test_save_has_amplifier(self):
        temperature_sensor = models.ResistanceTemperatureDeviceMeasurement()
        amplifier = models.ResistanceTemperatureDeviceAmplifier.objects.create()
        temperature_sensor.amplifier = amplifier
        temperature_sensor.save()
        self.assertIs(temperature_sensor.amplifier, amplifier)


class MashTunTest(TestCase):
    """Tests for the MashTun model."""

    def test_save_no_rtd(self):
        mash_tun = models.MashTun()
        self.assertIsNone(mash_tun.temperature_sensor)
        mash_tun.save()
        self.assertIsNotNone(mash_tun.temperature_sensor)

    def test_save_has_rtd(self):
        mash_tun = models.MashTun()
        temperature_sensor\
            = models.ResistanceTemperatureDeviceMeasurement.objects.create()
        mash_tun.temperature_sensor = temperature_sensor
        mash_tun.save()
        self.assertIs(mash_tun.temperature_sensor, temperature_sensor)


class HotLiquorTunTest(TestCase):
    """Tests for the HotLiquorTun model."""

    def test_save_no_rtd(self):
        hot_liquor_tun = models.HotLiquorTun()
        self.assertIsNone(hot_liquor_tun.temperature_sensor)
        hot_liquor_tun.save()
        self.assertIsNotNone(hot_liquor_tun.temperature_sensor)

    def test_save_has_rtd(self):
        hot_liquor_tun = models.HotLiquorTun()
        temperature_sensor\
            = models.ResistanceTemperatureDeviceMeasurement.objects.create()
        hot_liquor_tun.temperature_sensor = temperature_sensor
        hot_liquor_tun.save()
        self.assertIs(hot_liquor_tun.temperature_sensor, temperature_sensor)

    def test_save_no_heating_element(self):
        hot_liquor_tun = models.HotLiquorTun()
        self.assertIsNone(hot_liquor_tun.heating_element)
        hot_liquor_tun.save()
        self.assertIsNotNone(hot_liquor_tun.heating_element)

    def test_save_has_heating_element(self):
        hot_liquor_tun = models.HotLiquorTun()
        heating_element = models.HeatingElement.objects.create()
        hot_liquor_tun.heating_element = heating_element
        hot_liquor_tun.save()
        self.assertIs(hot_liquor_tun.heating_element, heating_element)


class MockKubernetesREST(kubernetes.client.rest.RESTClientObject):
    """Mocks the Kubernetes underlying REST interface.

    Intercepts the simple REST API calls so we can get good coverage calling all
    intermediate logic like sanitization.
    """

    def request(self, method, url, query_params=None, headers=None,
                body=None, post_params=None, _preload_content=True,
                _request_timeout=None):
        del query_params, headers, post_params, _preload_content
        del _request_timeout
        return urllib3.response.HTTPResponse(
            '{} request at {}: {}'.format(method, url, body))


@patch('kubernetes.client.api_client.RESTClientObject', MockKubernetesREST)
@patch('joulia.settings.PRODUCTION_HOST', True)
class BrewhouseTest(TestCase):
    """Test for the Brewhouse model."""

    def test_active_no_recipe_instances(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        self.assertFalse(brewhouse.active)

    def test_active_one_active_recipe_instance(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertTrue(brewhouse.active)

    def test_active_one_inactive_recipe_instance(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=False)
        self.assertFalse(brewhouse.active)

    def test_active_recipe_instance_one_active(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertEquals(brewhouse.active_recipe_instance, recipe_instance)

    def test_active_recipe_instance_one_inactive(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe = models.Recipe.objects.create(name="Bar")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=False)
        self.assertIsNone(brewhouse.active_recipe_instance)

    def test_save_user_and_token_good(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz", user=user,
                                     token=token)
        user_count_start = User.objects.count()
        token_count_start = Token.objects.count()

        brewhouse.save()
        self.assertEquals(User.objects.count(), user_count_start)
        self.assertEquals(Token.objects.count(), token_count_start)

    def test_save_token_does_not_exist(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz", user=user)
        user_count_start = User.objects.count()
        token_count_start = Token.objects.count()

        brewhouse.save()
        self.assertEquals(User.objects.count(), user_count_start)
        self.assertEquals(Token.objects.count(), token_count_start + 1)
        self.assertEquals(brewhouse.token.user, user)

    def test_save_user_does_not_exist(self):
        group = Group.objects.create(name="Foo")
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz")
        user_count_start = User.objects.count()
        token_count_start = Token.objects.count()

        brewhouse.save()
        self.assertEquals(User.objects.count(), user_count_start + 1)
        self.assertEquals(Token.objects.count(), token_count_start + 1)
        self.assertIn(brewhouse.user, brewing_company.group.user_set.all())

    def test_save_user_bad_group_count(self):
        group = Group.objects.create(name="Foo")
        group_bad = Group.objects.create(name="bad")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        user.groups.add(group_bad)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz", user=user,
                                     token=token)
        with self.assertRaises(models.InvalidUserError):
            brewhouse.save()

    def test_save_user_in_wrong_group(self):
        group = Group.objects.create(name="Foo")
        group_bad = Group.objects.create(name="bad")
        user = User.objects.create(username="foo-user")
        user.groups.add(group_bad)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz", user=user,
                                     token=token)
        with self.assertRaises(models.InvalidUserError):
            brewhouse.save()

    def test_save_token_for_wrong_user(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        user_bad = User.objects.create(username="bad-user")
        token = Token.objects.create(user=user_bad)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse(brewery=brewery, name="Baz", user=user,
                                     token=token)
        with self.assertRaises(models.InvalidUserError):
            brewhouse.save()

    def test_str(self):
        brewery = models.Brewery.objects.create(name="Foo")
        brewhouse = models.Brewhouse.objects.create(name="Bar", brewery=brewery)
        recipe = models.Recipe.objects.create(name="Baz")
        models.RecipeInstance.objects.create(
            recipe=recipe, brewhouse=brewhouse, active=True)
        self.assertRegexpMatches(str(brewhouse), "\[Bar - Foo\]\(#\d+\)")

    def test_save_no_boil_kettle(self):
        brewhouse = models.Brewhouse()
        self.assertIsNone(brewhouse.boil_kettle)
        brewhouse.save()
        self.assertIsNotNone(brewhouse.boil_kettle)

    def test_save_has_boil_kettle(self):
        brewhouse = models.Brewhouse()
        boil_kettle = models.HotLiquorTun.objects.create()
        brewhouse.boil_kettle = boil_kettle
        brewhouse.save()
        self.assertIs(brewhouse.boil_kettle, boil_kettle)

    def test_save_no_mash_tun(self):
        brewhouse = models.Brewhouse()
        self.assertIsNone(brewhouse.mash_tun)
        brewhouse.save()
        self.assertIsNotNone(brewhouse.mash_tun)

    def test_save_has_mash_tun(self):
        brewhouse = models.Brewhouse()
        mash_tun = models.MashTun.objects.create()
        brewhouse.mash_tun = mash_tun
        brewhouse.save()
        self.assertIs(brewhouse.mash_tun, mash_tun)

    def test_save_no_pump(self):
        brewhouse = models.Brewhouse()
        self.assertIsNone(brewhouse.main_pump)
        brewhouse.save()
        self.assertIsNotNone(brewhouse.main_pump)

    def test_save_has_pump(self):
        brewhouse = models.Brewhouse()
        main_pump = models.Pump.objects.create()
        brewhouse.main_pump = main_pump
        brewhouse.save()
        self.assertIs(brewhouse.main_pump, main_pump)

    def test_save_create_simulation(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse.objects.create(
            brewery=brewery, name="Baz", user=user, token=token, simulated=True)

        self.assertTrue(brewhouse.simulated)
        self.assertIsNotNone(brewhouse.simulated_deployment_name)
        self.assertIsNotNone(brewhouse.simulated_secret_name)

    def test_delete_simulation(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse.objects.create(
            brewery=brewery, name="Baz", user=user, token=token, simulated=True)
        brewhouse.delete()

    def test_delete_simulation_on_simulation_removal(self):
        group = Group.objects.create(name="Foo")
        user = User.objects.create(username="foo-user")
        user.groups.add(group)
        token = Token.objects.create(user=user)
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company,
                                                name="Bar")
        brewhouse = models.Brewhouse.objects.create(
            brewery=brewery, name="Baz", user=user, token=token, simulated=True)

        self.assertTrue(brewhouse.simulated)
        self.assertIsNotNone(brewhouse.simulated_deployment_name)
        self.assertIsNotNone(brewhouse.simulated_secret_name)

        brewhouse.simulated = False
        brewhouse.save()

        self.assertFalse(brewhouse.simulated)
        self.assertIsNone(brewhouse.simulated_deployment_name)
        self.assertIsNone(brewhouse.simulated_secret_name)


class BeerStyleTest(TestCase):
    """Tests for the BeerStyle model."""

    def test_str(self):
        beer_style = models.BeerStyle.objects.create(name="Foo")
        self.assertEquals(str(beer_style), "Foo")


class YeastIngredientTest(TestCase):
    """Tests for the YeastIngredient model."""

    def test_initialize_average_attenuation(self):
        yeast = models.YeastIngredient.objects.create(
            average_attenuation=0.5)
        self.assertAlmostEqual(yeast.low_attenuation, 0.5)
        self.assertAlmostEqual(yeast.high_attenuation, 0.5)

    def test_average_attentuation(self):
        yeast = models.YeastIngredient(
            low_attenuation=0.7, high_attenuation=0.8)
        self.assertAlmostEqual(yeast.average_attenuation, 0.75)

    def test_initialize_average_abv_tolerance(self):
        yeast = models.YeastIngredient.objects.create(
            average_abv_tolerance=0.10)
        self.assertAlmostEqual(yeast.low_abv_tolerance, 0.10)
        self.assertAlmostEqual(yeast.high_abv_tolerance, 0.10)

    def test_average_abv_tolerance(self):
        yeast = models.YeastIngredient(
            low_abv_tolerance=0.05, high_abv_tolerance=0.10)
        self.assertAlmostEqual(yeast.average_abv_tolerance, 0.075)


class RecipeTest(TestCase):
    """Tests for the Recipe model."""

    def test_str(self):
        style = models.BeerStyle.objects.create(name="Bar")
        recipe = models.Recipe.objects.create(name="Foo", style=style)
        self.assertEquals(str(recipe), "Foo(Bar)")

    def test_original_gravity(self):
        recipe = models.Recipe.objects.create(volume=5.0)
        us_2row = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.036, name="US 2Row")
        crystal_malt = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.035, name="Crystal Malt")
        models.MaltIngredientAddition.objects.create(
            ingredient=us_2row, amount=4535.92, recipe=recipe)  # 10 pounds.
        models.MaltIngredientAddition.objects.create(
            ingredient=crystal_malt, amount=453.592, recipe=recipe)  # 1 pound.
        self.assertAlmostEqual(recipe.original_gravity, 1.079, 3)

    def test_original_gravity_efficiency(self):
        recipe = models.Recipe.objects.create(
            volume=5.0, brewhouse_efficiency=0.72)
        us_2row = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.036, name="US 2Row")
        crystal_malt = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.035, name="Crystal Malt")
        models.MaltIngredientAddition.objects.create(
            ingredient=us_2row, amount=4535.92, recipe=recipe)  # 10 pounds.
        models.MaltIngredientAddition.objects.create(
            ingredient=crystal_malt, amount=453.592, recipe=recipe)  # 1 pound.
        self.assertAlmostEqual(recipe.original_gravity, 1.057, 3)

    def test_final_gravity(self):
        yeast = models.YeastIngredient.objects.create(average_attenuation=0.75)
        recipe = models.Recipe.objects.create(volume=5.0, yeast=yeast)
        # Enough to give 1.08 OG.
        malt = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.1, name="Fake ingredient")
        models.MaltIngredientAddition.objects.create(
            ingredient=malt, amount=1814.37, recipe=recipe)
        self.assertAlmostEqual(recipe.original_gravity, 1.08, 3)

        self.assertAlmostEqual(recipe.final_gravity, 1.02, 3)

    def test_abv(self):
        yeast = models.YeastIngredient.objects.create(average_attenuation=0.75)
        recipe = models.Recipe.objects.create(volume=5.0, yeast=yeast)
        # Enough to give 1.08 OG.
        malt = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.1, name="Fake ingredient")
        models.MaltIngredientAddition.objects.create(
            ingredient=malt, amount=1814.37, recipe=recipe)
        self.assertAlmostEqual(recipe.original_gravity, 1.08, 3)
        self.assertAlmostEqual(recipe.final_gravity, 1.02, 3)

        self.assertAlmostEqual(recipe.abv, 0.07875, 5)

    def test_original_gravity_no_volume(self):
        recipe = models.Recipe.objects.create(volume=0.0)
        self.assertEquals(recipe.original_gravity, 0.0)

    def test_ibu(self):
        recipe = models.Recipe.objects.create(volume=5.0)

        us_2row = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.036, name="US 2Row")
        # Enough to get 1.08.
        models.MaltIngredientAddition.objects.create(
            ingredient=us_2row, amount=5000.0, recipe=recipe)

        perle = models.BitteringIngredient.objects.create(
            alpha_acid_weight=0.064, name="Perle")
        liberty = models.BitteringIngredient.objects.create(
            alpha_acid_weight=0.046, name="Liberty")
        models.BitteringIngredientAddition.objects.create(
            ingredient=perle, amount=42.5243, recipe=recipe, time_added=60.0,
            step_added=models.BREWING_STEP_CHOICES__BOIL)  # 1.5 ounces.
        models.BitteringIngredientAddition.objects.create(
            ingredient=liberty, amount=28.3495, recipe=recipe, time_added=15.0,
            step_added=models.BREWING_STEP_CHOICES__BOIL)  # 1 ounce.
        models.BitteringIngredientAddition.objects.create(
            ingredient=liberty, amount=28.3495, recipe=recipe, time_added=60.0,
            step_added=models.BREWING_STEP_CHOICES__WHIRLPOOL)  # 1 ounce.
        self.assertAlmostEqual(recipe.ibu, 31.576, 1)

    def test_ibu_no_volume(self):
        recipe = models.Recipe.objects.create(volume=0.0)
        self.assertEquals(recipe.ibu, 0.0)

    def test_srm(self):
        recipe = models.Recipe.objects.create(volume=5.0)

        us_2row = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.036, name="US 2Row", color=2.0)
        crystal_malt = models.MaltIngredient.objects.create(
            potential_sg_contribution=1.035, name="Crystal Malt, 60L",
            color=60.0)

        models.MaltIngredientAddition.objects.create(
            ingredient=us_2row, amount=4535.92, recipe=recipe)  # 10 pounds.
        models.MaltIngredientAddition.objects.create(
            ingredient=crystal_malt, amount=453.592, recipe=recipe)  # 1 pound.

        self.assertAlmostEqual(recipe.srm, 9.99, 2)

    def test_srm_no_volume(self):
        recipe = models.Recipe.objects.create(volume=0.0)
        self.assertEquals(recipe.srm, 0.0)


class MashPointTest(TestCase):
    """Tests for the MashPoint model."""

    def setUp(self):
        self.recipe = models.Recipe.objects.create(name="Foo")

    def test_add_new_mash_point_increments_index(self):
        mash_point_1 = models.MashPoint.objects.create(recipe=self.recipe)
        self.assertEquals(mash_point_1.index, 0)
        mash_point_2 = models.MashPoint.objects.create(recipe=self.recipe)
        self.assertEquals(mash_point_2.index, 1)

    def test_add_new_mash_point_increments_index_without_using_length(self):
        models.MashPoint.objects.create(recipe=self.recipe, index=1)
        mash_point = models.MashPoint.objects.create(recipe=self.recipe)
        self.assertEquals(mash_point.index, 2)

    def test_raise_runtime_error_when_saving_duplicate_index(self):
        models.MashPoint.objects.create(recipe=self.recipe)
        with self.assertRaisesRegex(RuntimeError,
                                    "cannot be saved with the same index"):
            models.MashPoint.objects.create(recipe=self.recipe, index=0)

    def test_reordering_mash_points(self):
        mash_point_1 = models.MashPoint.objects.create(recipe=self.recipe)
        mash_point_2 = models.MashPoint.objects.create(recipe=self.recipe)
        mash_point_1.index = None
        mash_point_1.save()
        mash_point_2.index = 0
        mash_point_2.save()
        mash_point_1.index = 1
        mash_point_1.save()
        mash_point_1.refresh_from_db()
        self.assertEquals(mash_point_1.index, 1)
        self.assertEquals(mash_point_2.index, 0)

    def test_saving_self_does_not_conflict_index(self):
        mash_point = models.MashPoint.objects.create(recipe=self.recipe)
        mash_point.save()


class RecipeInstanceTest(TestCase):
    """Tests for the RecipeInstance model."""
    def setUp(self):
        self.recipe = models.Recipe.objects.create(name="Foo")

    def test_save_inactive_new_no_active(self):
        models.RecipeInstance.objects.create(recipe=self.recipe, active=False)

    def test_save_active_new_no_active(self):
        models.RecipeInstance.objects.create(recipe=self.recipe, active=True)

    def test_save_inactive_new_no_active_inactive_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)

    def test_save_active_new_no_active_inactive_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)

    def test_save_active_new_no_active_active_already_fails(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        with self.assertRaisesRegex(RuntimeError, "already active"):
            models.RecipeInstance.objects.create(
                recipe=self.recipe, brewhouse=brewhouse, active=True)

    def test_save_inactive_new_no_active_active_already(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=False)

    def test_save_active_self(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe, brewhouse=brewhouse, active=True)
        recipe_instance.save()

    def test_str_active_without_brewhouse(self):
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe, active=True)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (None) ACTIVE")

    def test_str_active_with_brewhouse(self):
        brewhouse = models.Brewhouse.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe,
            brewhouse=brewhouse, active=True)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (Bar) ACTIVE")

    def test_str_inactive_without_brewhouse(self):
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe, active=False)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (None) INACTIVE")

    def test_str_inactive_with_brewhouse(self):
        brewhouse = models.Brewhouse.objects.create(name="Bar")
        recipe_instance = models.RecipeInstance.objects.create(
            date=datetime.datetime(2017, 4, 7), recipe=self.recipe,
            brewhouse=brewhouse, active=False)
        recipe_instance.refresh_from_db()
        self.assertEquals(str(recipe_instance),
                          "Foo - 2017-04-07 (Bar) INACTIVE")


class AssetSensorTest(TestCase):
    """Tests for the AssetSensor model."""

    def test_str(self):
        brewhouse = models.Brewhouse.objects.create(name="Foo")
        sensor = models.AssetSensor.objects.create(name="Bar",
                                                   brewhouse=brewhouse)
        self.assertEquals(str(sensor), "Foo-Bar")

    def test_str_no_brewhouse(self):
        sensor = models.AssetSensor.objects.create(name="Bar")
        self.assertEquals(str(sensor), "None-Bar")

class TimeSeriesDataPointTest(TestCase):
    """Tests for the TimeSeriesDataPoint model."""

    def test_str(self):
        sensor = models.AssetSensor.objects.create(name="Foo")
        datapoint = models.TimeSeriesDataPoint(
            sensor=sensor, value=1.0,
            time=datetime.datetime(2017, 4, 7, 21, 3, 59))
        self.assertEquals(str(datapoint), "Foo - 1.0 @ 2017-04-07 21:03:59")
