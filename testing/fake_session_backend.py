"""Provides a mock Session backend for manipulating the session in tests to
achieve specific states like a signed in user."""

from django.contrib.sessions.backends.base import SessionBase
from django.test import override_settings


class SessionStore(SessionBase):
    """A fake session store storing data as a class variable. Not a very safe
    usage, but helps with messing with the session in tests. Use decorator
    @fake_session_cleanup."""
    _session = {}
    __managed = False

    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)

    def __setattr__(self, key, value):
        if not self.__managed:
            raise RuntimeError(
                "You must wrap a test method using fake_session_backend with"
                " the @fake_session_cleanup decorator.")

        super(SessionStore, self).__setattr__(key, value)

    def save(self, must_create=False):
        pass

    def delete(self, session_key=None):
        pass

    @classmethod
    def manage_store(cls):
        cls.__managed = True

    @classmethod
    def reset_store(cls):
        cls.__managed = False
        cls._session = {}


def fake_session_cleanup(func):
    """Decorator used to wrap tests using fake_session_backend.SessionStore to
    mark it as currently managed, and then resets it to an empty state after the
    test is complete. Add it to any test methods using the SessionStore."""
    def wrapper(*args, **kwargs):
        SessionStore.manage_store()
        func(*args, **kwargs)
        SessionStore.reset_store()

    return wrapper


def test_with_fake_session_backend(func):
    """Decorator used to override django settings with using the SessionStore
    in this module, cleaning the session up, etc.
    """

    @override_settings(SESSION_ENGINE='testing.fake_session_backend')
    @override_settings(AUTHENTICATION_BACKENDS=[
        'testing.fake_model_backend.NoHashModelBackend'])
    @fake_session_cleanup
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper
