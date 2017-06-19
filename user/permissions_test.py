"""Tests for the user.permissions module."""

from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import Mock

from user import permissions


class IsUserTest(TestCase):
    """Tests for IsUser permissions class."""

    def test_has_permission(self):
        permission = permissions.IsUser()
        user = User.objects.create(username="user")
        request = Mock()
        request.user = user
        view = None

        self.assertTrue(permission.has_object_permission(
            request, view, user.userpreferences))

    def test_does_not_have_permission(self):
        permission = permissions.IsUser()
        user = User.objects.create(username="user")
        other_user = User.objects.create(username="bar")
        request = Mock()
        request.user = other_user
        view = None

        self.assertFalse(permission.has_object_permission(
            request, view, user.userpreferences))
