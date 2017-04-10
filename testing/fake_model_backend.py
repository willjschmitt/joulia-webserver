"""Providea a fake Model Backend, which will disable a lot of security checks on
a user, which is useful for tests only.
"""

from django.contrib.auth.backends import ModelBackend


class UserWrapper(object):
    """Looks like a User, except ignores methods in IGNORE_METHODS. This is an
    insecure wrapper and should only be used for tests."""
    IGNORE_METHODS = ('get_session_auth_hash',)

    def __init__(self, user):
        self.user = user

    def __getattr__(self, attr):
        if attr in self.IGNORE_METHODS:
            raise AttributeError("Faking non-existence of this method.")
        return getattr(self.user, attr)

    def __eq__(self, other):
        return self.user == other


class NoHashModelBackend(ModelBackend):
    """Overrides get_user method to provide a test-wrapped User, which disables
    lots of checks for unit testing. Use only with special care and never in
    production.
    """

    def get_user(self, user_id):
        user = super(NoHashModelBackend, self).get_user(user_id)
        return UserWrapper(user)
