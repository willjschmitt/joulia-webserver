'''
Created on Jun 20, 2016

@author: Will
'''
'''
Created on Apr 9, 2016

@author: William
'''

from .views import TimeSeriesSocketHandler

urlpatterns = [
    (r"/live/timeseries/socket/", TimeSeriesSocketHandler),
]