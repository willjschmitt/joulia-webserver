"""Django REST framework filters for convenience use.
"""
import operator

from django.db import models
from django.utils import six
from functools import reduce
from rest_framework.compat import distinct
from rest_framework.filters import SearchFilter


class SearchOrIdFilter(SearchFilter):
    """A search field, which uses the search parameter for the normal behavior
    from SearchFilter with an OR filter against a provided 'id' url parameter.

    Useful for when a query should return a list of searched values as well as
    the already selected value by id.
    """

    def filter_queryset(self, request, queryset, view):
        """This is a minor reimplementation of the filter_queryset on
        SearchFilter from DjangoRestFramework, but adds a query against the id
        if present.
        """
        search_fields = getattr(view, 'search_fields', None)
        search_terms = self.get_search_terms(request)

        # If not doing any searching, at least filter on id.
        pk = request.query_params.get('id', None)
        if not search_fields or not search_terms:
            if pk is not None:
                return queryset.filter(pk=pk)
            else:
                return queryset

        orm_lookups = [
            self.construct_search(six.text_type(search_field))
            for search_field in search_fields
        ]

        base = queryset
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            # Always add pk as an OR match.
            if pk is not None:
                queries.append(models.Q(pk=pk))
            queryset = queryset.filter(reduce(operator.or_, queries))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this if possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset
