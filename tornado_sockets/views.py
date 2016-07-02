'''
Created on Jun 20, 2016

@author: Will
'''
import tornado.escape
import tornado.web
import tornado.websocket

from django.db.models.signals import post_save
from django.dispatch import receiver

from brewery.models import Brewery
from brewery.models import AssetSensor
from brewery.models import TimeSeriesDataPoint
from brewery.serializers import TimeSeriesDataPointSerializer

# from django.db.models import ForeignKey

import logging
logger = logging.getLogger(__name__)

class TimeSeriesSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200
    
    subscriptions = {}

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    '''
    Core websocket functions
    '''
    def open(self):
        logger.info("New websocket connection incomming {}".format(self))
        TimeSeriesSocketHandler.waiters.add(self)
        logger.info("returning {}".format(self))

    def on_close(self):
        TimeSeriesSocketHandler.waiters.remove(self)
        for subscription in TimeSeriesSocketHandler.subscriptions.itervalues():
            try: subscription.remove(self)
            except KeyError: pass
            
    def on_message(self, message):
        parsedMessage = tornado.escape.json_decode(message)
        logger.debug('parsed message is {}'.format(parsedMessage))
        #we are subscribing to a 
        if 'subscribe' in parsedMessage:
            self.subscribe(parsedMessage)
        else:
            self.newData(parsedMessage)
        
    '''
    Message helper functions
    '''      
    def subscribe(self,parsedMessage):
        logger.debug('Subscribing')
        if 'sensor' not in parsedMessage:
            parsedMessage['sensor'] = AssetSensor.objects.get(sensor=parsedMessage['sensor'],asset=1)#TODO: programatically get asset
            
        key = (parsedMessage['recipe_instance'],parsedMessage['sensor'])
        if key not in TimeSeriesSocketHandler.subscriptions: 
            TimeSeriesSocketHandler.subscriptions[key] = set()
        if self not in TimeSeriesSocketHandler.subscriptions[key]: #protect against double subscriptions
            TimeSeriesSocketHandler.subscriptions[key].add(self)
    
#     def newData(self,parsedMessage):
#         logging.debug('New data')
#         fields = ('recipe_instance','sensor','time','value',)
#         newDataPoint = {}
#         for fieldName in fields:
#             field = TimeSeriesDataPoint._meta.get_field(fieldName)
#             if field.is_relation:
#                 newDataPoint[fieldName] = field.related_model.objects.get(pk=parsedMessage[fieldName])
#             else:
#                 newDataPoint[fieldName] = parsedMessage[fieldName]
#         TimeSeriesDataPoint(**newDataPoint).save()
        
    '''
    Cache handling helper functions
    '''        
    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]
     
    @classmethod
    def send_updates(cls, newDataPoint):
        logger.info("sending message to %d waiters", len(cls.waiters))
        key = (newDataPoint.recipe_instance.pk,newDataPoint.sensor.pk)
        if key in cls.subscriptions:
            for waiter in cls.subscriptions[key]:
                try:
                    serializer = TimeSeriesDataPointSerializer(newDataPoint)
                    waiter.write_message(serializer.data)
                except:
                    logger.error("Error sending message", exc_info=True)
        
@receiver(post_save, sender=TimeSeriesDataPoint)
def timeSeriesWatcher(sender, instance, **kwargs):
    logger.debug("Got new datapoint {}".format(instance))
    TimeSeriesSocketHandler.update_cache(instance)
    TimeSeriesSocketHandler.send_updates(instance)
