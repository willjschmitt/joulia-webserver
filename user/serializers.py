"""Django rest framework serializers for the user app.
"""
from rest_framework import serializers

from user import models


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Standard serializer for UserPreferences model."""
    class Meta:
        model = models.UserPreferences
        fields = '__all__'
