from django.core.exceptions import ObjectDoesNotExist

from .models import Asset,AssetSensor
from .models import TimeSeriesDataPoint

from .serializers import TimeSeriesDataPointSerializer

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

import logging

# # Create your views here.
# class MainHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.render("index.html",brewery=Brewery.objects.get(pk=1))

class TimeSeriesNewHandler(generics.CreateAPIView):
    queryset = TimeSeriesDataPoint.objects.all()
    serializer_class = TimeSeriesDataPointSerializer

class TimeSeriesIdentifyHandler(APIView):
    def post(self,request,*args,**kwargs):
        try:#see if we can ge an existing AssetSensor
            sensor = AssetSensor.objects.get(name=request.POST['name'],asset=Asset.objects.get(id=1))#TODO: programatically get asset
        except ObjectDoesNotExist: #otherwise create one for recording data
            logging.debug('Creating new asset sensor {} for asset {}'.format(request.POST['name'],1))
            sensor = AssetSensor(name=request.POST['name'],asset=Asset.objects.get(id=1))#TODO: programatically get asset
            sensor.save()
        return Response({'sensor':sensor.pk})