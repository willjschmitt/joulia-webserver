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

    def get_object(self):
        # Overridden to always return the UserPreferences associated with the
        # request's user.
        return models.UserPreferences.objects.get(user=self.request.user)
