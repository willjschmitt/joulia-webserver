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
