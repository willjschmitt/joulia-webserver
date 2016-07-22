'''
Created on Apr 9, 2016

@author: William
'''

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"live/timeseries/new/$", views.TimeSeriesNewHandler.as_view()),
    url(r"live/timeseries/identify/$", views.TimeSeriesIdentifyHandler.as_view()),
    
    url(r"brewery/launch$", views.launch_recipe_instance),
    url(r"brewery/end$", views.end_recipe_instance),
    
    url(r"api/recipe/$", views.RecipeListView.as_view()),
    url(r"api/recipeInstance/$", views.RecipeInstanceListView.as_view()),
    url(r"api/brewhouse/$", views.BrewhouseListView.as_view()),
    url(r"api/brewhouse/(?P<pk>[0-9]+)/$", views.BrewhouseDetailView.as_view()),
    url(r"api/brewery/$", views.BreweryListView.as_view()),
    url(r"api/brewery/(?P<pk>[0-9]+)/$", views.BreweryDetailView.as_view()),
    url(r"api/beerStyle/", views.BeerStyleListView.as_view()),
]