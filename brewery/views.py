"""Views for the django ``Brewery`` application.
"""
# pylint: disable=too-many-ancestors

from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import JsonResponse
import logging
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from brewery import models
from brewery import permissions
from brewery import serializers
from joulia import http


LOGGER = logging.getLogger(__name__)


class BrewingCompanyApiMixin(APIView):
    """Common REST API view information for ``BrewingCompany`` model."""
    serializer_class = serializers.BrewingCompanySerializer
    permission_classes = (IsAuthenticated, permissions.IsMember)

    def get_queryset(self):
        return models.BrewingCompany.objects.filter(
            group__user=self.request.user)


class BrewingCompanyListView(BrewingCompanyApiMixin,
                             generics.ListCreateAPIView):
    """List and Create REST API view for ``BrewingCompany`` model."""
    pass


class BrewingCompanyDetailView(BrewingCompanyApiMixin,
                               generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``BrewingCompany``model.
    """
    pass


class BreweryApiMixin(APIView):
    """Common REST API view information for ``Brewery`` model."""
    serializer_class = serializers.BrewerySerializer
    permission_classes = (IsAuthenticated, permissions.IsMemberOfBrewingCompany)

    def get_queryset(self):
        return models.Brewery.objects.filter(
            company__group__user=self.request.user)


class BreweryListView(BreweryApiMixin, generics.ListCreateAPIView):
    """List and Create REST API view for ``Brewery`` model."""
    pass


class BreweryDetailView(BreweryApiMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``Brewery``model."""
    pass


class BrewhouseApiMixin(APIView):
    """Common REST API view information for ``Brewhouse`` model."""
    serializer_class = serializers.BrewhouseSerializer
    permission_classes = (IsAuthenticated, permissions.IsMemberOfBrewery)
    filter_fields = ('id', 'brewery',)

    def get_queryset(self):
        return models.Brewhouse.objects.filter(
            brewery__company__group__user=self.request.user)


class BrewhouseListView(BrewhouseApiMixin, generics.ListCreateAPIView):
    """List and Create REST API view for ``Brewhouse`` model."""
    pass


class BrewhouseDetailView(BrewhouseApiMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``Brewhouse``model."""
    pass


class BeerStyleListView(generics.ListAPIView):
    """List and Create REST API view for ``BeerStyle`` model."""
    queryset = models.BeerStyle.objects.all()
    serializer_class = serializers.BeerStyleSerializer


class RecipeAPIMixin(APIView):
    """Common REST API view information for ``Recipe`` model."""
    serializer_class = serializers.RecipeSerializer
    permission_classes = (IsAuthenticated, permissions.IsMemberOfBrewingCompany)

    def get_queryset(self):
        return models.Recipe.objects.filter(
            company__group__user=self.request.user)


class RecipeListView(RecipeAPIMixin, generics.ListCreateAPIView):
    """List and Create REST API view for ``Recipe`` model."""
    pass


class RecipeDetailView(RecipeAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``Recipe`` model."""
    pass


class MashPointAPIMixin(APIView):
    """Common REST API view information for ``MashPoint`` model."""
    serializer_class = serializers.MashPointSerializer
    permission_classes = (IsAuthenticated, permissions.OwnsRecipe)
    filter_fields = ('id', 'recipe',)

    def get_queryset(self):
        return models.MashPoint.objects.filter(
            recipe__company__group__user=self.request.user).order_by('index')


class MashPointListView(MashPointAPIMixin, generics.ListCreateAPIView):
    """List and create REST API for ``MashPoint`` model."""
    pass


class MashPointDetailView(MashPointAPIMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, Update, and Destroy REST API view for ``MashPoint`` model."""
    pass


class RecipeInstanceApiMixin(APIView):
    """Common REST API view information for ``RecipeInstance`` model."""
    serializer_class = serializers.RecipeInstanceSerializer
    permission_classes = (IsAuthenticated, permissions.OwnsRecipe)
    filter_fields = ('id', 'active', 'brewhouse',)

    def get_queryset(self):
        return models.RecipeInstance.objects.filter(
            recipe__company__group__user=self.request.user)


class RecipeInstanceListView(RecipeInstanceApiMixin,
                             generics.ListCreateAPIView):
    """List and Create REST API view for ``RecipeInstance`` model."""
    pass


class RecipeInstanceDetailView(RecipeInstanceApiMixin,
                               generics.RetrieveUpdateAPIView):
    """Retrieve and Update REST API view for ``RecipeInstance`` model."""
    pass


class TimeSeriesNewHandler(generics.CreateAPIView):
    """Create REST API view for ``TimeSeriesDataPoint`` model."""
    serializer_class = serializers.TimeSeriesDataPointSerializer
    permission_classes = (IsAuthenticated, permissions.OwnsSensor)

    def get_queryset(self):
        return models.TimeSeriesDataPoint.objects.filter(
            sensor__brewhouse__brewery__company__group__user=
            self.request.user)


class TimeSeriesIdentifyHandler(APIView):
    """Identifies a time series group by the name of an AssetSensor.

    Can only be handled as a POST request.
    """

    @staticmethod
    def post(request):
        """Identifies a time series group by the name of an AssetSensor.

        If the AssetSensor does not yet exist, creates it.

        Args:
            recipe_instance: (Optional) POST argument with the
                recipe_instance pk. Used to retrieve the Brewhouse equipment
                associated with the request. Used for some cases when the
                equipment has more readily available access to the
                recipe_instance rather than the Brewhouse directly.
            brewhouse: (Optional): POST argument with the Brewhouse pk. Required
                if recipe_instance is not submitted.
            name: Name for the AssetSensor to be used in the time series data.
                See AssetSensor for more information on naming.

        Returns:
            JsonResponse with the pk to the sensor as the property "sensor".
            Response status is 200 if just returning object and 201 if needed to
            create a new AssetSensor.
        """
        name = request.data['name']

        if 'recipe_instance' in request.data:
            recipe_instance_id = request.data['recipe_instance']
            recipe_instance = models.RecipeInstance.objects.get(
                id=recipe_instance_id)
            brewhouse = recipe_instance.brewhouse
        else:
            brewhouse_id = request.data['brewhouse']
            brewhouse = models.Brewhouse.objects.get(id=brewhouse_id)

        if not permissions.is_member_of_brewing_company(
                request.user, brewhouse.brewery.company):
            return HttpResponseForbidden(
                'Access not permitted to brewing equipment.')

        # See if we can get an existing AssetSensor.
        try:
            sensor = models.AssetSensor.objects.get(name=name,
                                                    brewhouse=brewhouse)
            status_code = status.HTTP_200_OK
        # Otherwise create one for recording data
        except ObjectDoesNotExist:
            LOGGER.debug('Creating new asset sensor %s for asset %s',
                         name, brewhouse)
            sensor = models.AssetSensor(name=name, brewhouse=brewhouse)
            sensor.save()
            status_code = status.HTTP_201_CREATED

        response = JsonResponse({'sensor': sensor.pk})
        response.status_code = status_code
        return response


class BrewhouseIdByToken(APIView):
    """Retrieves the brewhouse ID for a user authenticated with a Token."""

    @staticmethod
    def get(request):
        try:
            brewhouse = request.user.auth_token.brewhouse
            return JsonResponse({'brewhouse': brewhouse.pk})
        except ObjectDoesNotExist:
            return HttpResponseForbidden()


class BrewhouseLaunchView(APIView):
    """Launches a recipe instance on a Brewhouse."""

    @staticmethod
    def post(request):
        brewhouse_pk = http.get_post_value_or_400(request, 'brewhouse')
        recipe_pk = http.get_post_value_or_400(request, 'recipe')

        brewhouse = http.get_object_or_404(models.Brewhouse, brewhouse_pk)
        if not permissions.IsMemberOfBrewery().has_object_permission(
                request, None, brewhouse):
            raise http.HTTP403("No permission to access requested brewhouse.")
        recipe = http.get_object_or_404(models.Recipe, recipe_pk)
        if not permissions.IsMemberOfBrewingCompany().has_object_permission(
                request, None, recipe):
            raise http.HTTP403("No permission to access requested recipe.")

        recipe_instance = models.RecipeInstance.objects.create(
            brewhouse=brewhouse, recipe=recipe, active=True)

        return JsonResponse({"id": recipe_instance.pk})


class BrewhouseEndView(APIView):
    """Ends a recipe instance on a Brewhouse."""

    @staticmethod
    def post(request):
        recipe_instance_pk = http.get_post_value_or_400(request,
                                                        'recipe_instance')
        recipe_instance = http.get_object_or_404(models.RecipeInstance,
                                                 recipe_instance_pk)

        if not permissions.OwnsRecipe().has_object_permission(
                request, None, recipe_instance):
            raise http.HTTP403(
                "No permission to access requested recipe_instance.")

        recipe_instance.active = False
        recipe_instance.save()
        return HttpResponse()
