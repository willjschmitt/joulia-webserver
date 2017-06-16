"""Tests for the brewery.views module.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import Mock

from user import views


class UserPreferencesApiMixinTest(TestCase):
    """Tests for UserPreferencesApiMixin."""

    def test_get_queryset(self):
        user = User.objects.create(username="foo")

        view = views.UserPreferencesApiMixin()
        view.request = Mock(user=user)
        got = view.get_queryset()
        self.assertIn(user.userpreferences, got)

    def test_get_queryset_excludes_other_users(self):
        user = User.objects.create(username="foo")
        other_user = User.objects.create(username="bar")

        view = views.UserPreferencesApiMixin()
        view.request = Mock(user=user)
        got = view.get_queryset()
        self.assertIn(user.userpreferences, got)
        self.assertNotIn(other_user.userpreferences, got)
