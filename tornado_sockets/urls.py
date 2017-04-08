"""Urls for tornado_sockets app which handles all asynchronous end points."""
import tornado_sockets.views.recipe_instance
from tornado_sockets.views import timeseries

urlpatterns = [
    (r"/live/timeseries/socket/", timeseries.TimeSeriesSocketHandler),
    (r"/live/recipeInstance/start/",
     tornado_sockets.views.recipe_instance.RecipeInstanceStartHandler),
    (r"/live/recipeInstance/end/",
     tornado_sockets.views.recipe_instance.RecipeInstanceEndHandler),
]