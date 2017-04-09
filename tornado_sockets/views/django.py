"""Base classes and mixin's for Tornado views to work with django for things
like authentication.
"""

from rest_framework.settings import api_settings
from tornado.web import RequestHandler

from tornado_sockets.utils import get_current_user


class DjangoAuthenticatedRequestHandler(RequestHandler):
    """Uses the django rest framework authentication handlers for the Tornado
    handlers, which are all asynchronous and done through XHR or other API-like
    operations rather than browser page requests.
    """

    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES

    def get_current_user(self):
        """Gets current user from Django site for use in Tornado views."""
        return get_current_user(self)
    # TODO(wschmitt): Extend this with token authentication using code similar
    # to below possibly.
    # def get_current_user(self):
    #     """Gets the current user using the django rest framework
    #     `authentication_classes`. The classes default to those from the
    #     settings, but can always be overridden in child classes.
    #     """
    #     print("yooooo")
    #     authenticators = (auth() for auth in self.authentication_classes)
    #     self.auth = None
    #     for authenticator in authenticators:
    #         try:
    #             user_auth_tuple = authenticator.authenticate(self)
    #         except:
    #             pass
    #
    #         if user_auth_tuple is not None:
    #             self._authenticator = authenticator
    #             user = user_auth_tuple[0]
    #             self.auth = user_auth_tuple[1]
    #             return user

    @property
    def META(self):
        """Mocks a conversion of the tornado headers into django headers, since
        tornado doesn't have really middleware that manipulates the incoming
        headers. Particularly, this function takes the "Authorization" header
        incoming from tornado and returns a dictionary with "HTTP_AUTHORIZATION"
        containing the same value.
        """
        tornado_auth_header = self.request.headers['Authorization']
        headers = {'HTTP_AUTHORIZATION': tornado_auth_header}
        return headers

    @property
    def _request(self):
        return self
