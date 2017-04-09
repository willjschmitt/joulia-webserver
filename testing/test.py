"""Provides testing base class for use throughout the site."""

from django.test import TestCase

from testing.fake_session_backend import SessionStore


class JouliaTestCase(TestCase):
    """Base TestCase adding abilities to log in the user for Tornado
    RequestHandler's.
    """

    # TODO(willjschmitt): Consider if the DRF force_login could support this
    # without client usage.
    @staticmethod
    def force_tornado_login(user):
        store = SessionStore()
        store['_auth_user_id'] = user.pk
        store['_auth_user_backend'] = (
            'testing.fake_model_backend.NoHashModelBackend')
        store.save()