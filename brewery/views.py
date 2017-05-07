"""Views for the django ``Brewery`` application.
"""
# pylint: disable=too-many-ancestors

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
import logging
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from tornado.escape import json_decode

from brewery import models
from brewery import permissions
from brewery import serializers


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


class BeerStyleListView(generics.ListCreateAPIView):
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
    queryset = models.TimeSeriesDataPoint.objects.all()
    serializer_class = serializers.TimeSeriesDataPointSerializer


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


@login_required  
def launch_recipe_instance(request):
    """Starts a RecipeInstance on a given Brewhouse.

    Must be submitted as a POST request.

    Args:
        recipe: POST argument for the recipe to run on the Brewhouse
        brewhouse: POST argument for the Brewhouse to launch the recipe on.

    Raises:
        HttpResponseNotAllowed: if the request is not submitted as POST.
        HttpResponseForbidden: if the user is not associated with the
            BrewingCompany that owns the Brewhouse requested.
        HttpResponseBadRequest: if the brewery is already active.
    Returns:
        JsonResponse if the brewhouse is successfully activated. Contains the pk
        to the newly instantiated instance as property "recipe_instance".
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json_decode(request.body)
    recipe = models.Recipe.objects.get(pk=data['recipe'])
    brewhouse = models.Brewhouse.objects.get(pk=data['brewhouse'])
    brewery = brewhouse.brewery

    if not permissions.is_member_of_brewing_company(request.user,
                                                    brewery.company):
        return HttpResponseForbidden(
            'Access not permitted to brewing equipment.')

    active_recipe_count = models.RecipeInstance.objects.filter(
        brewhouse=brewhouse, active=True).count()
    if active_recipe_count != 0:
        return HttpResponseBadRequest('Brewery is already active')

    else:
        new_instance = models.RecipeInstance(
            recipe=recipe, brewhouse=brewhouse, active=True)
        new_instance.save()
        return JsonResponse({'recipe_instance': new_instance.pk})


@login_required  
def end_recipe_instance(request):
    """Stops an already running RecipeInstance.

    Must be submitted as a POST request.

    Args:
        recipe_instance: POST argument for the recipe_instance currently running
            on equipment.

    Raises:
        HttpResponseNotAllowed: if the request is not submitted as POST.
        HttpResponseForbidden: if the user is not associated with the
            BrewingCompany that owns the Brewhouse associated with the
            recipe_instance.
        HttpResponseBadRequest: if the recipe_instance is not active.
    Returns:
        JsonResponse if the brewhouse is successfully deactivated. Response is
        an empty Json object.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json_decode(request.body)
    recipe_instance = models.RecipeInstance.objects.get(
        pk=data['recipe_instance'])
    brewhouse = recipe_instance.brewhouse
    brewery = brewhouse.brewery

    if not permissions.is_member_of_brewing_company(
            request.user, brewery.company):
        return HttpResponseForbidden(
            'Access not permitted to brewing equipment.')

    if not recipe_instance.active:
        return HttpResponseBadRequest(
            'Recipe instance requested was not an active instance.')

    recipe_instance.active = False
    recipe_instance.save()

    return JsonResponse({})
