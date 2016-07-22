'''
Created on Apr 9, 2016

@author: William
'''

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"live/timeseries/new/$", views.TimeSeriesNewHandler.as_view()),
    url(r"live/timeseries/identify/$", views.TimeSeriesIdentifyHandler.as_view()),
    
    url(r"launch$", views.launch_recipe_instance),
    url(r"end$", views.end_recipe_instance),
    
    url(r"api/recipe/$", views.RecipeListView.as_view()),
    url(r"api/recipeInstance/$", views.RecipeInstanceListView.as_view()),
    url(r"api/brewery/$", views.BreweryListView.as_view()),
    url(r"api/brewery/(?P<pk>[0-9]+)/$", views.BreweryDetailView.as_view()),
    url(r"api/brewingFacility/$", views.BrewingFacilityListView.as_view()),
    url(r"api/brewingFacility/(?P<pk>[0-9]+)/$", views.BrewingFacilityDetailView.as_view()),
    url(r"api/beerStyle/", views.BeerStyleListView.as_view()),
]