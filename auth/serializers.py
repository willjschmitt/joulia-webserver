"""Django rest framework serializers for the django auth models.
"""
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Standard serializer for django.contrib.auth.models.User model."""
    class Meta:
        model = User
        fields = ("email", "first_name", "groups", "last_name", "username")
