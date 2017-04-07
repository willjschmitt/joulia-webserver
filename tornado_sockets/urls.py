"""Urls for tornado_sockets app which handles all asynchronous end points."""

from tornado_sockets import views

urlpatterns = [
    (r"/live/timeseries/socket/", views.TimeSeriesSocketHandler),
    (r"/live/recipeInstance/start/", views.RecipeInstanceStartHandler),
    (r"/live/recipeInstance/end/", views.RecipeInstanceEndHandler),
]