"""Tests for the tornado_sockets.utils module.
"""

from django.contrib.auth.models import User

from testing.fake_session_backend import test_with_fake_session_backend
from testing.test import JouliaTestCase
from tornado_sockets import utils


class FakeTornadoView(object):
    def get_cookie(self, cookie_name):
        return "abcdefg"


class GetCurrentUserTest(JouliaTestCase):
    """Tests for get_current_user function."""

    @test_with_fake_session_backend
    def test_gets_user(self):
        user = User.objects.create(username="john_doe")

        self.force_tornado_login(user)

        view = FakeTornadoView()
        current_user = utils.get_current_user(view)
        # Order matters here for the assertEquals since current_user is a
        # special wrapper around User for the tests.
        self.assertEquals(current_user, user)
