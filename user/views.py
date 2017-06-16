"""Views for the django ``User`` application.
"""
# pylint: disable=too-many-ancestors

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from user import models
from user import permissions
from user import serializers

class UserPreferencesApiMixin(APIView):
    """Common REST API view information for ``UserPreferences`` model."""
    serializer_class = serializers.UserPreferencesSerializer
    permission_classes = (IsAuthenticated, permissions.IsUser)

    def get_queryset(self):
        return models.UserPreferences.objects.filter(user=self.request.user)


class BrewingCompanyListView(UserPreferencesApiMixin,
                             generics.ListCreateAPIView):
    """List and Create REST API view for ``UserPreferences`` model."""
    pass


class BrewingCompanyDetailView(UserPreferencesApiMixin,
                               generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``UserPreferences``model.
    """
    pass
