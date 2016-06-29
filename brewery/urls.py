'''
Created on Apr 9, 2016

@author: William
'''

from django.conf.urls import url
from .views import TimeSeriesNewHandler,TimeSeriesIdentifyHandler

from .views import RecipeListView,BreweryListView

urlpatterns = [
    url(r"live/timeseries/new/$", TimeSeriesNewHandler.as_view()),
    url(r"live/timeseries/identify/$", TimeSeriesIdentifyHandler.as_view()),
    
    
    url(r"api/recipe/$", RecipeListView.as_view()),
    url(r"api/brewery/$", BreweryListView.as_view()),
]