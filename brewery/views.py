from django.core.exceptions import ObjectDoesNotExist

from .models import Asset,AssetSensor
from .models import TimeSeriesDataPoint
from .models import Recipe
from .models import Brewery
from .models import BeerStyle

from .serializers import TimeSeriesDataPointSerializer
from .serializers import RecipeSerializer
from .serializers import BrewerySerializer
from .serializers import BeerStyleSerializer

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

import logging

class BeerStyleListView(generics.ListCreateAPIView):
    queryset = BeerStyle.objects.all()
    serializer_class = BeerStyleSerializer

class RecipeListView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    
class BreweryListView(generics.ListCreateAPIView):
    queryset = Brewery.objects.all()
    serializer_class = BrewerySerializer

class TimeSeriesNewHandler(generics.CreateAPIView):
    queryset = TimeSeriesDataPoint.objects.all()
    serializer_class = TimeSeriesDataPointSerializer

class TimeSeriesIdentifyHandler(APIView):
    def post(self,request,*args,**kwargs):
        try:#see if we can ge an existing AssetSensor
            sensor = AssetSensor.objects.get(name=request.data['name'],asset=Asset.objects.get(id=1))#TODO: programatically get asset
        except ObjectDoesNotExist: #otherwise create one for recording data
            logging.debug('Creating new asset sensor {} for asset {}'.format(request.data['name'],1))
            sensor = AssetSensor(name=request.data['name'],asset=Asset.objects.get(id=1))#TODO: programatically get asset
            sensor.save()
        return Response({'sensor':sensor.pk})