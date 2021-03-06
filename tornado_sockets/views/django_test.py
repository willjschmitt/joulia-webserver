"""Tests for the tornado_sockets.django module.
"""

from django.test import Client
from django.contrib.auth.models import User
import logging
from rest_framework.authtoken.models import Token
from rest_framework import status
from tornado.httpclient import HTTPRequest
import tornado.ioloop
from tornado.testing import gen_test
from tornado.testing import AsyncTestCase
from tornado.testing import AsyncHTTPTestCase
import tornado.web
from tornado.websocket import websocket_connect

from tornado_sockets.views.django import DjangoAuthenticatedRequestHandler
from tornado_sockets.views.django import DjangoAuthenticatedWebSocketHandler

LOGGER = logging.getLogger(__name__)


class DjangoAuthenticatedRequestHandlerTest(AsyncHTTPTestCase):
    def setUp(self):
        super(DjangoAuthenticatedRequestHandlerTest, self).setUp()
        self.username = "john_doe"
        self.password = "abc123"
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.token = Token.objects.create(user=self.user)

    def tearDown(self):
        """Since we are not using django's unittest framework for these tests,
        we need to manually delete created objects in the database.
        """
        super(DjangoAuthenticatedRequestHandlerTest, self).tearDown()
        self.user.delete()
        self.token.delete()

    def get_app(self):
        class GetUserView(DjangoAuthenticatedRequestHandler):
            def get(self):
                got_user = self.get_current_user().pk
                want_user = int(self.get_query_argument("user"))
                if got_user != want_user:
                    self.set_status(status.HTTP_403_FORBIDDEN,
                                    "http://bit.ly/2qnDnf9")

        return tornado.web.Application(((r"/", GetUserView),))

    def test_gets_user_basic_auth(self):
        response = self.fetch(
            "/?user={}".format(self.user.pk), request_timeout=1,
            auth_username=self.username, auth_password=self.password)
        self.assertEquals(response.code, status.HTTP_200_OK)

    def test_gets_user_token_auth(self):
        response = self.fetch(
            "/?user={}".format(self.user.pk), request_timeout=1,
            headers={"Authorization": "Token {}".format(self.token.key)})
        self.assertEquals(response.code, status.HTTP_200_OK)

    def test_gets_user_session_auth(self):
        c = Client()
        response = c.post("/login/", data={"username": self.username,
                                           "password": self.password})
        cookies = response.cookies
        cookie_names = ("sessionid", "csrftoken",)
        cookie_header = "; ".join(
            "{}={}".format(name, cookies[name].value) for name in cookie_names)
        response = self.fetch(
            "/?user={}".format(self.user.pk), request_timeout=1,
            headers={
                "Cookie": cookie_header,
                "X-CSRFToken": cookies["csrftoken"].value})
        self.assertEquals(response.code, status.HTTP_200_OK)


class DjangoAuthenticatedWebSocketHandlerTest(AsyncHTTPTestCase):
    def setUp(self):
        super(DjangoAuthenticatedWebSocketHandlerTest, self).setUp()
        self.username = "john_doe"
        self.password = "abc123"
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.token = Token.objects.create(user=self.user)

    def tearDown(self):
        """Since we are not using django's unittest framework for these tests,
        we need to manually delete created objects in the database.
        """
        super(DjangoAuthenticatedWebSocketHandlerTest, self).tearDown()
        self.user.delete()
        self.token.delete()

    def get_app(self):
        class GetUserView(DjangoAuthenticatedWebSocketHandler):
            def open(self):
                user = self.get_current_user()
                self.write_message(str(user.pk))

        return tornado.web.Application(((r"/", GetUserView),))

    @gen_test
    def test_gets_user_basic_auth(self):
        request = HTTPRequest(self.get_url("/").replace("http", "ws"),
                              auth_username=self.username,
                              auth_password=self.password)
        conn = yield websocket_connect(request)
        response = yield conn.read_message()
        self.assertEquals(User.objects.get(pk=int(response)), self.user)

    @gen_test
    def test_gets_user_token_auth(self):
        request = HTTPRequest(
            self.get_url("/").replace("http", "ws"),
            headers={"Authorization": "Token {}".format(self.token.key)})
        conn = yield websocket_connect(request)
        response = yield conn.read_message()
        self.assertEquals(User.objects.get(pk=int(response)), self.user)

    @gen_test
    def test_gets_user_session_auth(self):
        c = Client()
        response = c.post("/login/", data={"username": self.username,
                                           "password": self.password})
        cookies = response.cookies
        cookie_names = ("sessionid", "csrftoken",)
        cookie_header = "; ".join(
            "{}={}".format(name, cookies[name].value) for name in cookie_names)
        request = HTTPRequest(
            self.get_url("/").replace("http", "ws"),
            headers={
                "Cookie": cookie_header,
                "X-CSRFToken": cookies["csrftoken"].value})
        conn = yield websocket_connect(request)
        response = yield conn.read_message()
        self.assertEquals(User.objects.get(pk=int(response)), self.user)
