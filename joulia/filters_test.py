"""Tests for joulia.filters module."""

from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase

from joulia import filters


class SearchOrIdFilterTest(TestCase):
    """Tests for the joulia.filters.SearchOrIdFilter."""

    def setUp(self):
        self.filter = filters.SearchOrIdFilter()

    def test_filter_queryset_with_search(self):
        user1 = User.objects.create(first_name="john", username="foo")
        User.objects.create(first_name="larry", username="bar")
        queryset = User.objects.all()
        self.assertEquals(len(queryset), 2)

        view = Mock()
        view.search_fields = ("first_name",)

        request = Mock()
        request.query_params = {"search": user1.first_name}

        filtered = self.filter.filter_queryset(request, queryset, view)
        self.assertEquals(len(filtered), 1)
        self.assertEquals(filtered[0], user1)

    def test_filter_queryset_with_id(self):
        user1 = User.objects.create(first_name="john", username="foo")
        User.objects.create(first_name="larry", username="bar")
        queryset = User.objects.all()
        self.assertEquals(len(queryset), 2)

        view = Mock()
        view.search_fields = ("first_name",)

        request = Mock()
        request.query_params = {"id": user1.pk}

        filtered = self.filter.filter_queryset(request, queryset, view)
        self.assertEquals(len(filtered), 1)
        self.assertEquals(filtered[0], user1)

    def test_filter_queryset_with_id_and_search(self):
        user1 = User.objects.create(first_name="john", username="foo")
        User.objects.create(first_name="larry", username="bar")
        queryset = User.objects.all()
        self.assertEquals(len(queryset), 2)

        view = Mock()
        view.search_fields = ("first_name",)

        request = Mock()
        request.query_params = {"search": user1.first_name, "id": user1.pk}

        filtered = self.filter.filter_queryset(request, queryset, view)
        self.assertEquals(len(filtered), 1)
        self.assertEquals(filtered[0], user1)

    def test_filter_queryset_with_id_and_search_different(self):
        user1 = User.objects.create(first_name="john", username="foo")
        user2 = User.objects.create(first_name="larry", username="bar")
        queryset = User.objects.all()
        self.assertEquals(len(queryset), 2)

        view = Mock()
        view.search_fields = ("first_name",)

        request = Mock()
        request.query_params = {"search": user2.first_name, "id": user1.pk}

        filtered = self.filter.filter_queryset(request, queryset, view)
        self.assertEquals(len(filtered), 2)
        self.assertIn(user1, filtered)
        self.assertIn(user2, filtered)
