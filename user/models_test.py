"""Tests for the user.models module.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from user import models


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
