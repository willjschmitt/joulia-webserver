"""Tests for the user.models module.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from user import models


class UserPreferencesTest(TestCase):
    """Test for the UserPreferences model."""

    def test_str(self):
        user = User.objects.create(username="foo")
        user_preferences = models.UserPreferences.objects.get(user=user)
        # This might be flaky if the str method for User's changes.
        self.assertEquals(str(user_preferences), "foo - User Preferences")


class UserPreferencesCreatorTest(TestCase):
    """Tests for the user_preferences_creator receiver."""

    def test_new_user(self):
        user = User.objects.create(username="foo")

        user_preferences = models.UserPreferences.objects.get(user=user)
        self.assertEquals(user_preferences.user, user)
        self.assertEquals(user.userpreferences, user_preferences)

    def test_existing_user(self):
        user = User.objects.create(username="foo")
        user.save()

        user_preferences = models.UserPreferences.objects.get(user=user)
        self.assertEquals(user_preferences.user, user)
        self.assertEquals(user.userpreferences, user_preferences)
