"""Django rest framework permissions for the user app rest end points.
"""

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from user import models


class IsUser(permissions.BasePermission):
    """Checks the current user is associated with the current requested
    UserPreferences instance.
    """
    def has_object_permission(self, request, view, user_preferences):
        return request.user == user_preferences.user
