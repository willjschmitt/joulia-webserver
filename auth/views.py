"""Views for the django ``auth`` application.
"""
# pylint: disable=too-many-ancestors

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth import serializers


class UserView(APIView):
    """Common REST API view information for ``BrewingCompany`` model."""

    def get(self, request, format=None):
        """Returns the currently logged in user."""
        user = request.user
        if not user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            serializer = serializers.UserSerializer(user)
            return Response(serializer.data)
