from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseForbidden

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from .permissions import IsMemberOfBrewingCompany,is_member_of_brewing_company

from . import models
from . import serializers

import logging
import json


class BeerStyleListView(generics.ListCreateAPIView):
    queryset = models.BeerStyle.objects.all()
    serializer_class = serializers.BeerStyleSerializer

class RecipeListView(generics.ListCreateAPIView):
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer

class RecipeInstanceListView(generics.ListCreateAPIView):
    queryset = models.RecipeInstance.objects.all()
    serializer_class = serializers.RecipeInstanceSerializer
    filter_fields = ('id', 'active','brewery',)
    
class BreweryApiView():
    queryset = models.Brewery.objects.all()
    serializer_class = serializers.BrewerySerializer
    permission_classes = (IsAuthenticated,IsMemberOfBrewingCompany)
class BreweryListView(BreweryApiView,generics.ListCreateAPIView): pass
class BreweryDetailView(BreweryApiView,generics.RetrieveUpdateDestroyAPIView): pass

class BrewingFacilityApiView():
    queryset = models.BrewingFacility.objects.all()
    serializer_class = serializers.BrewingFacilitySerializer
    permission_classes = (IsAuthenticated,)#,IsMemberOfBrewingCompany)
class BrewingFacilityListView(BrewingFacilityApiView,generics.ListCreateAPIView): pass
class BrewingFacilityDetailView(BrewingFacilityApiView,generics.RetrieveUpdateDestroyAPIView): pass
    

class TimeSeriesNewHandler(generics.CreateAPIView):
    queryset = models.TimeSeriesDataPoint.objects.all()
    serializer_class = serializers.TimeSeriesDataPointSerializer

class TimeSeriesIdentifyHandler(APIView):
    def post(self,request,*args,**kwargs):
        try:#see if we can ge an existing AssetSensor
            sensor = models.AssetSensor.objects.get(name=request.data['name'],
                                                    brewery=models.Brewery.objects.get(id=1))#TODO: programatically get asset
        except ObjectDoesNotExist: #otherwise create one for recording data
            logging.debug('Creating new asset sensor {} for asset {}'.format(request.data['name'],1))
            sensor = models.AssetSensor(name=request.data['name'],
                                        brewery=models.Brewery.objects.get(id=1))#TODO: programatically get asset
            sensor.save()
        return Response({'sensor':sensor.pk})
  
@login_required  
def launch_recipe_instance(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    recipe = models.Recipe.objects.get(pk=data['recipe'])
    brewery = models.Brewery.objects.get(pk=data['brewery'])
    
    if not is_member_of_brewing_company(request.user,brewery):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    if models.RecipeInstance.objects.filter(brewery=brewery,
                                     active=True).count()!=0:
        return HttpResponseBadRequest('Brewery is already active')

    else:
        new_instance = models.RecipeInstance(recipe=recipe,brewery=brewery,active=True)
        new_instance.save()
        return HttpResponse()
    
@login_required  
def end_recipe_instance(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    recipe_instance = models.RecipeInstance.objects.get(pk=data['recipe_instance'])
    
    if not is_member_of_brewing_company(request.user,recipe_instance.brewery):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    recipe_instance = recipe_instance
    recipe_instance.active = False
    recipe_instance.save()
    
    return HttpResponse()