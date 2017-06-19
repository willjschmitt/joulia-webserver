"""Views for the django ``User`` application.
"""
# pylint: disable=too-many-ancestors

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from user import models
from user import permissions
from user import serializers


class UserPreferencesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``UserPreferences``model.
    """
    serializer_class = serializers.UserPreferencesSerializer
    permission_classes = (IsAuthenticated, permissions.IsUser)

    def get_queryset(self):
        return models.UserPreferences.objects.filter(user=self.request.user)

    def get_object(self):
        # Overridden to always return the UserPreferences associated with the
        # request's user.
        return self.get_queryset().get(user=self.request.user)
