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

        view = views.UserPreferencesDetailView()
        view.request = Mock(user=user)
        got = view.get_object()
        self.assertEquals(user.userpreferences, got)

    def test_get_queryset_excludes_other_users(self):
        user = User.objects.create(username="foo")
        other_user = User.objects.create(username="bar")

        view = views.UserPreferencesDetailView()
        view.request = Mock(user=user)
        got = view.get_object()
        self.assertEquals(user.userpreferences, got)
        self.assertNotEquals(other_user.userpreferences, got)
