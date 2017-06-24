"""Tests for the auth.views module.
"""

from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from rest_framework import status


class TestUserView(TestCase):
    """Tests for views.UserView."""

    def setUp(self):
        self.c = Client()

    def test_get_user_logged_in(self):
        user = User.objects.create_user("john", "john@example.com", "smith",
                                        first_name="john", last_name="smith")
        self.c.post('/login/', {'username': 'john', 'password': 'smith'})
        response = self.c.get('/auth/api/user/',
                              content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        want = {
            "id": user.pk,
            "first_name": "john",
            "last_name": "smith",
            "email": "john@example.com",
            "groups": [],
            "username": "john",
        }
        self.assertEqual(response_data, want)

    def test_get_user_logged_out(self):
        response = self.c.get('/auth/api/user/',
                              content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = response.json()
        want = {}
        self.assertEqual(response_data, want)
