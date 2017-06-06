"""Tests for joulia.http module.
"""

from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import QueryDict
from django.test import TestCase
from unittest.mock import Mock

from joulia import http


class GetPostValueOr400Test(TestCase):
    def test_key_missing(self):
        request = Mock()
        request.POST = QueryDict('foo=bar')
        with self.assertRaises(http.HTTP400):
            http.get_post_value_or_400(request, 'bar')

    def test_key_present(self):
        request = Mock()
        request.POST = QueryDict('foo=bar')
        value = http.get_post_value_or_400(request, 'foo')
        self.assertEquals(value, 'bar')


class GetObjectOr404Test(TestCase):
    def test_object_exists(self):
        # Using User as a simple example, but it could be any model.
        user = User.objects.create(username="foo")
        got = http.get_object_or_404(User, user.pk)
        self.assertEquals(user, got)

    def test_object_does_not_exist(self):
        # Using User as a simple example, but it could be any model.
        with self.assertRaises(http.HTTP404):
            http.get_object_or_404(User, 3489572934)


class ConvertHTTPExceptionsMiddleware(TestCase):
    def test_okay_response(self):
        response = Mock()
        get_response = lambda request: response
        middleware = http.ConvertHTTPExceptionsMiddleware(get_response)
        request = Mock()
        self.assertIs(middleware(request), response)

    def test_400_response(self):
        def get_response(_):
            raise http.HTTP400()
        middleware = http.ConvertHTTPExceptionsMiddleware(get_response)
        request = Mock()
        response = middleware(request)
        self.assertEquals(type(response), HttpResponseBadRequest)

    def test_404_response(self):
        def get_response(_):
            raise http.HTTP404()
        middleware = http.ConvertHTTPExceptionsMiddleware(get_response)
        request = Mock()
        response = middleware(request)
        self.assertEquals(type(response), HttpResponseNotFound)
