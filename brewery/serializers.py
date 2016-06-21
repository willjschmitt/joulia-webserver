'''
Created on Jun 20, 2016

@author: Will
'''
from rest_framework import serializers

from .models import TimeSeriesDataPoint

class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSeriesDataPoint