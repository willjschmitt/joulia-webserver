"""Utility functions for the tornado_sockets app.
"""

from django.conf import settings
import django.contrib.auth
from importlib import import_module


def get_current_user(info):
    """Gets the currently logged user from django into tornado views.

    Args:
        info: Likely a tornado view, which can provide a cookie via get_cookie
            method.

    Returns:
        User making request.
    """
    engine = import_module(settings.SESSION_ENGINE)
    session_key = str(info.get_cookie(settings.SESSION_COOKIE_NAME))

    class Dummy(object):
        pass

    django_request = Dummy()
    django_request.session = engine.SessionStore(session_key)
    user = django.contrib.auth.get_user(django_request)
    return user
