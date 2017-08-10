"""URLS for the brewery app."""

from django.conf.urls import url

from brewery import views

urlpatterns = [
    url(r"api/joulia_controller_release/$",
        views.JouliaControllerReleaseListView.as_view()),
    url(r"api/joulia_controller_release/(?P<pk>[0-9]+)/$",
        views.JouliaControllerReleaseDetailView.as_view()),

    url(r"api/brewingCompany/$", views.BrewingCompanyListView.as_view()),
    url(r"api/brewingCompany/(?P<pk>[0-9]+)/$",
        views.BrewingCompanyDetailView.as_view()),
    url(r"api/brewery/$", views.BreweryListView.as_view()),
    url(r"api/brewery/(?P<pk>[0-9]+)/$", views.BreweryDetailView.as_view()),
    url(r"api/brewhouse/$", views.BrewhouseListView.as_view()),
    url(r"api/brewhouse/(?P<pk>[0-9]+)/$", views.BrewhouseDetailView.as_view()),
    url(r"api/brewhouse/launch/", views.BrewhouseLaunchView.as_view()),
    url(r"api/brewhouse/end/", views.BrewhouseEndView.as_view()),

    url(r"api/beerStyle/", views.BeerStyleListView.as_view()),
    url(r"api/recipe/$", views.RecipeListView.as_view()),
    url(r"api/recipe/(?P<pk>[0-9]+)/$", views.RecipeDetailView.as_view()),
    url(r"api/malt_ingredient/$", views.MaltIngredientListView.as_view()),
    url(r"api/malt_ingredient/(?P<pk>[0-9]+)/$",
        views.MaltIngredientDetailView.as_view()),
    url(r"api/bittering_ingredient/$",
        views.BitteringIngredientListView.as_view()),
    url(r"api/bittering_ingredient/(?P<pk>[0-9]+)/$",
        views.BitteringIngredientDetailView.as_view()),
    url(r"api/ingredient_addition/$",
        views.IngredientAdditionListView.as_view()),
    url(r"api/ingredient_addition/(?P<pk>[0-9]+)/$",
        views.IngredientAdditionDetailView.as_view()),
    url(r"api/mash_point/$", views.MashPointListView.as_view()),
    url(r"api/mash_point/(?P<pk>[0-9]+)/$",
        views.MashPointDetailView.as_view()),
    url(r"api/recipeInstance/$", views.RecipeInstanceListView.as_view()),
    url(r"api/recipeInstance/(?P<pk>[0-9]+)/$",
        views.RecipeInstanceDetailView.as_view()),

    url(r"api/brewhouse_from_token/$", views.BrewhouseIdByToken.as_view()),
]