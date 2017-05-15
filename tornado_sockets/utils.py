"""Utility functions for the tornado_sockets app.
"""

from django.conf import settings
from django.contrib.auth import get_user
from importlib import import_module


class _FakeAuthenticatedRequest(object):
    """Mocks a django request with the session set by a tornado view cookie."""
    def __init__(self, view):
        print(settings.SESSION_ENGINE)
        engine = import_module(settings.SESSION_ENGINE)
        session_key = str(view.get_cookie(settings.SESSION_COOKIE_NAME))
        self.session = engine.SessionStore(session_key)


def get_current_user(view):
    """Gets the currently logged user from django into tornado views.

    Args:
        view: A tornado view, which can provide a cookie via get_cookie method.

    Returns:
        User making request.
    """
    django_request = _FakeAuthenticatedRequest(view)
    return get_user(django_request)
