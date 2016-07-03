'''
Created on Jun 20, 2016

@author: Will
'''
'''
Created on Apr 9, 2016

@author: William
'''

from . import views

urlpatterns = [
    (r"/live/timeseries/socket/", views.TimeSeriesSocketHandler),
    
    (r"/live/recipeInstance/start/", views.RecipeInstanceStartHandler),
    (r"/live/recipeInstance/end/", views.RecipeInstanceEndHandler),
]