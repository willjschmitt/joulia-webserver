"""URLS for the brewery app."""

from django.conf.urls import url

from brewery import views

urlpatterns = [
    url(r"live/timeseries/new/$", views.TimeSeriesNewHandler.as_view()),
    url(r"live/timeseries/identify/$",
        views.TimeSeriesIdentifyHandler.as_view()),
    
    url(r"brewhouse/launch$", views.launch_recipe_instance),
    url(r"brewhouse/end$", views.end_recipe_instance),
    
    url(r"api/brewingCompany/$", views.BrewingCompanyListView.as_view()),
    url(r"api/brewingCompany/(?P<pk>[0-9]+)/$",
        views.BrewingCompanyDetailView.as_view()),
    url(r"api/brewery/$", views.BreweryListView.as_view()),
    url(r"api/brewery/(?P<pk>[0-9]+)/$", views.BreweryDetailView.as_view()),
    url(r"api/brewhouse/$", views.BrewhouseListView.as_view()),
    url(r"api/brewhouse/(?P<pk>[0-9]+)/$", views.BrewhouseDetailView.as_view()),
    
    url(r"api/beerStyle/", views.BeerStyleListView.as_view()),
    url(r"api/recipe/$", views.RecipeListView.as_view()),
    url(r"api/recipe/(?P<pk>[0-9]+)/$", views.RecipeDetailView.as_view()),
    url(r"api/mash_point/$", views.MashPointListView.as_view()),
    url(r"api/mash_point/(?P<pk>[0-9]+)/$",
        views.MashPointDetailView.as_view()),
    url(r"api/recipeInstance/$", views.RecipeInstanceListView.as_view()),
    url(r"api/recipeInstance/(?P<pk>[0-9]+)/$",
        views.RecipeInstanceDetailView.as_view()),
]