"""Tests for the joulia.views module."""

from rest_framework import status
from rest_framework.test import APITestCase


class HelloWorldTest(APITestCase):
    """Tests for HelloWorld view."""

    def test_success(self):
        response = self.client.get("/")
        self.assertTrue(status.is_success(response.status_code))
