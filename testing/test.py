"""Provides testing base class for use throughout the site."""

from django.test import TestCase
from rest_framework.authtoken.models import Token
from unittest.mock import Mock


class JouliaTestCase(TestCase):
    """Base TestCase adding abilities to log in the user for Tornado
    RequestHandler's.
    """

    def setUp(self):
        super(JouliaTestCase, self).setUp()
        self.app = Mock()
        self.app.ui_methods = {}
        self.request = Mock()
        self.request.headers = {}
        self.request.cookies = {}
        self.request.arguments = {}

    def force_tornado_login(self, user):
        token = Token.objects.create(user=user)
        self.request.headers["Authorization"] = "Token {}".format(token.key)
