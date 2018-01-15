"""Base classes and mixin's for Tornado views to work with django for things
like authentication.
"""

from django.conf import settings
from django.contrib.auth import get_user
from django.http.request import HttpRequest
from importlib import import_module
from rest_framework.request import Request
from rest_framework.settings import api_settings
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler


class DjangoAuthenticatedRequestHandler(RequestHandler):
    """Uses the django rest framework authentication handlers for the Tornado
    handlers, which are all asynchronous and done through XHR or other API-like
    operations rather than browser page requests.
    """

    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES

    def get_current_user(self):
        """Overrides to get the currently logged user from django into tornado
        views.
        """
        django_request = DjangoMockedRequest(self)
        django_request.user = get_user(django_request)
        authenticators = (auth() for auth in self.authentication_classes)
        rest_framework_request = Request(django_request,
                                         authenticators=authenticators)
        user = rest_framework_request.user
        return user


class DjangoAuthenticatedWebSocketHandler(DjangoAuthenticatedRequestHandler,
                                          WebSocketHandler):
    """Wraps DjangoAuthenticatedRequestHandler for websocket authentication."""
    pass


class DjangoMockedRequest(HttpRequest):
    """A Django HttpRequest with the correct settings applied to it as if it
    were created by a WSGI request directly.
    """

    def __init__(self, tornado_request):
        super(DjangoMockedRequest, self).__init__()
        self._tornado_view = tornado_request

        self.method = self._tornado_view.request.method
        self._set_session()
        self._set_cookies()
        self._configure_headers()

    def _set_session(self):
        engine = import_module(settings.SESSION_ENGINE)
        session_cookie_name = settings.SESSION_COOKIE_NAME
        session_key = str(self._tornado_view.get_cookie(session_cookie_name))
        self.session = engine.SessionStore(session_key)

    def _set_cookies(self):
        cookies_to_set = ("csrftoken", "sessionid",)
        for cookie_to_set in cookies_to_set:
            self.COOKIES[cookie_to_set] = str(
                self._tornado_view.get_cookie(cookie_to_set))

    def _configure_headers(self):
        header_conversions = ("AUTHORIZATION", "X_CSRFTOKEN",)
        for header_name, header in self._tornado_view.request.headers.items():
            sanitized = header_name.replace("-", "_").upper()
            if sanitized in header_conversions:
                new_header_name = "HTTP_{}".format(sanitized)
                header = self._tornado_view.request.headers[header_name]
                self.META[new_header_name] = header
