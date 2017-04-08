"""Tests for the tornado_sockets.utils module.
"""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from testing.fake_session_backend import fake_session_cleanup
from testing.fake_session_backend import SessionStore
from tornado_sockets import utils


class FakeTornadoView(object):
    def get_cookie(self, cookie_name):
        return "abcdefg"


class GetCurrentUserTest(TestCase):
    """Tests for get_current_user function."""

    @override_settings(SESSION_ENGINE='testing.fake_session_backend')
    @override_settings(AUTHENTICATION_BACKENDS=[
        'testing.fake_model_backend.NoHashModelBackend'])
    @fake_session_cleanup
    def test_gets_user(self):
        user = User.objects.create(username="john_doe")

        store = SessionStore()
        store['_auth_user_id'] = user.pk
        store['_auth_user_backend'] = (
            'testing.fake_model_backend.NoHashModelBackend')
        store.save()

        view = FakeTornadoView()
        current_user = utils.get_current_user(view)
        # Order matters here for the assertEquals since current_user is a
        # special wrapper around User for the tests.
        self.assertEquals(current_user, user)
