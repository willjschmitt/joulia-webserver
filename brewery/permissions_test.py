"""Tests for the brewery.permissions module."""

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import Mock

from brewery import models
from brewery import permissions


class IsMemberTest(TestCase):
    """Tests for IsMember permissions class."""

    def test_has_permission(self):
        permission = permissions.IsMember()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)

        self.assertTrue(permission.has_object_permission(
            request, view, brewing_company))

    def test_does_not_have_permission(self):
        permission = permissions.IsMember()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)

        self.assertFalse(permission.has_object_permission(
            request, view, brewing_company))


class IsMemberOfBrewingCompanyTest(TestCase):
    """Tests for IsMemberOfBrewingCompany permissions class."""

    def test_has_permission(self):
        permission = permissions.IsMemberOfBrewingCompany()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        brewery = models.Brewery(company=brewing_company)

        self.assertTrue(permission.has_object_permission(
            request, view, brewery))

    def test_does_not_have_permission(self):
        permission = permissions.IsMemberOfBrewingCompany()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        brewery = models.Brewery(company=brewing_company)

        self.assertFalse(permission.has_object_permission(
            request, view, brewery))


class IsMemberOfBreweryTest(TestCase):
    """Tests for IsMemberOfBrewery permissions class."""

    def test_has_permission(self):
        permission = permissions.IsMemberOfBrewery()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        brewery = models.Brewery(company=brewing_company)
        brewhouse = models.Brewhouse(brewery=brewery)

        self.assertTrue(permission.has_object_permission(
            request, view, brewhouse))

    def test_does_not_have_permission(self):
        permission = permissions.IsMemberOfBrewery()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        brewery = models.Brewery(company=brewing_company)
        brewhouse = models.Brewhouse(brewery=brewery)

        self.assertFalse(permission.has_object_permission(
            request, view, brewhouse))


class OwnsRecipeTest(TestCase):
    """Tests for OwnsRecipe permissions class."""

    def test_has_permission(self):
        permission = permissions.OwnsRecipe()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        recipe = models.Recipe(company=brewing_company)
        recipe_instance = models.RecipeInstance(recipe=recipe)
        self.assertTrue(permission.has_object_permission(
            request, view, recipe_instance))

    def test_does_not_have_permission(self):
        permission = permissions.OwnsRecipe()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany(group=group)
        recipe = models.Recipe(company=brewing_company)
        recipe_instance = models.RecipeInstance(recipe=recipe)
        self.assertFalse(permission.has_object_permission(
            request, view, recipe_instance))


class OwnsSensorTest(TestCase):
    """Tests for OwnsSensor permissions class."""

    def test_has_permission(self):
        permission = permissions.OwnsSensor()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company)
        brewhouse = models.Brewhouse.objects.create(brewery=brewery)
        recipe = models.Recipe.objects.create(company=brewing_company)
        recipe_instance = models.RecipeInstance.objects.create(recipe=recipe)
        sensor = models.AssetSensor.objects.create(brewhouse=brewhouse)
        data_point = models.TimeSeriesDataPoint.objects.create(
            sensor=sensor, recipe_instance=recipe_instance)
        self.assertTrue(permission.has_object_permission(
            request, view, data_point))

    def test_does_not_have_permission(self):
        permission = permissions.OwnsSensor()
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        request = Mock()
        request.user = user
        view = None
        brewing_company = models.BrewingCompany.objects.create(group=group)
        brewery = models.Brewery.objects.create(company=brewing_company)
        brewhouse = models.Brewhouse.objects.create(brewery=brewery)
        recipe = models.Recipe.objects.create(company=brewing_company)
        recipe_instance = models.RecipeInstance.objects.create(recipe=recipe)
        sensor = models.AssetSensor.objects.create(brewhouse=brewhouse)
        data_point = models.TimeSeriesDataPoint.objects.create(
            sensor=sensor, recipe_instance=recipe_instance)
        self.assertFalse(permission.has_object_permission(
            request, view, data_point))


class IsMemberOfBrewingCompanyFunctionTest(TestCase):
    """Tests for is_member_of_brewing_company function."""

    def test_is_member(self):
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        group.user_set.add(user)
        brewing_company = models.BrewingCompany(group=group)
        self.assertTrue(permissions.is_member_of_brewing_company(
            user, brewing_company))

    def test_is_not_member(self):
        user = User.objects.create(username="user")
        group = Group.objects.create(name="group")
        brewing_company = models.BrewingCompany(group=group)
        self.assertFalse(permissions.is_member_of_brewing_company(
            user, brewing_company))

    def test_no_group(self):
        user = User.objects.create(username="user")
        brewing_company = models.BrewingCompany()
        self.assertFalse(permissions.is_member_of_brewing_company(
            user, brewing_company))