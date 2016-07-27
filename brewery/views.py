from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseForbidden

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from . import permissions

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
    filter_fields = ('id', 'active','brewhouse',)
    
class BrewhouseApiView():
    queryset = models.Brewhouse.objects.all()
    serializer_class = serializers.BrewhouseSerializer
    permission_classes = (IsAuthenticated,permissions.IsMemberOfBrewery)
    filter_fields = ('id', 'brewery', )
class BrewhouseListView(BrewhouseApiView,generics.ListCreateAPIView): pass
class BrewhouseDetailView(BrewhouseApiView,generics.RetrieveUpdateDestroyAPIView): pass

class BreweryApiView():
    queryset = models.Brewery.objects.all()
    serializer_class = serializers.BrewerySerializer
    permission_classes = (IsAuthenticated,permissions.IsMemberOfBrewingCompany)
class BreweryListView(BreweryApiView,generics.ListCreateAPIView): pass
class BreweryDetailView(BreweryApiView,generics.RetrieveUpdateDestroyAPIView): pass
    

class TimeSeriesNewHandler(generics.CreateAPIView):
    queryset = models.TimeSeriesDataPoint.objects.all()
    serializer_class = serializers.TimeSeriesDataPointSerializer

class TimeSeriesIdentifyHandler(APIView):
    def post(self,request,*args,**kwargs):
        try:#see if we can ge an existing AssetSensor
            if 'recipe_instance' in request.data:
                recipe_instance = models.RecipeInstance.objects.get(id=request.data['recipe_instance'])
                brewhouse = recipe_instance.brewhouse
            else:
                brewhouse = models.Brewhouse.objects.get(id=request.data['brewhouse'])
            
            sensor = models.AssetSensor.objects.get(name=request.data['name'],
                                                    brewery=brewhouse)
        except ObjectDoesNotExist: #otherwise create one for recording data
            logging.debug('Creating new asset sensor {} for asset {}'.format(request.data['name'],brewhouse))
            sensor = models.AssetSensor(name=request.data['name'],
                                        brewery=brewhouse)
            sensor.save()
        return Response({'sensor':sensor.pk})
  
@login_required  
def launch_recipe_instance(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    data = json.loads(request.body)
    recipe = models.Recipe.objects.get(pk=data['recipe'])
    brewhouse = models.Brewhouse.objects.get(pk=data['brewhouse'])
    brewery = brewhouse.brewery
    
    if not permissions.is_member_of_brewing_company(request.user,brewery):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    if models.RecipeInstance.objects.filter(brewhouse=brewhouse,
                                            active=True).count()!=0:
        return HttpResponseBadRequest('Brewery is already active')

    else:
        new_instance = models.RecipeInstance(recipe=recipe,brewhouse=brewhouse,active=True)
        new_instance.save()
        return JsonResponse({'recipe_instance':new_instance.pk})
    
@login_required  
def end_recipe_instance(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    recipe_instance = models.RecipeInstance.objects.get(pk=data['recipe_instance'])
    brewhouse = recipe_instance.brewhouse
    brewery = brewhouse.brewery
    
    if not permissions.is_member_of_brewing_company(request.user,brewery):
        return HttpResponseForbidden('Access not permitted to brewing equipment.')
    
    if not recipe_instance.active:
        return HttpResponseBadRequest('Recipe instance requested was not an active instance.')
    recipe_instance.active = False
    recipe_instance.save()
    
    return JsonResponse({})