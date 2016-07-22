'''
Created on Jun 20, 2016

@author: Will
'''
import tornado.escape
import tornado.web
import tornado.websocket
from tornado import gen
from tornado.concurrent import Future

from django.db.models.signals import post_save
from django.dispatch import receiver

from brewery.models import Brewery
from brewery.models import RecipeInstance
from brewery.models import AssetSensor
from brewery.models import TimeSeriesDataPoint
from brewery.serializers import TimeSeriesDataPointSerializer
from brewery.permissions import is_member_of_brewing_company

from .utils import get_current_user

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

        recipe_instance_pk = parsedMessage['recipe_instance']
        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)
        
        user = get_current_user(self)
        brewery = recipe_instance.brewery
        location = brewery.location
        if not is_member_of_brewing_company(user,location):
            logger.error("User {} attempted to access brewery "
                         "they do not have access to ({})".format(user,recipe_instance.brewery))
            return
        
        key = (recipe_instance_pk,parsedMessage['sensor'])
        if key not in TimeSeriesSocketHandler.subscriptions:
            TimeSeriesSocketHandler.subscriptions[key] = set()
        if self not in TimeSeriesSocketHandler.subscriptions[key]: #protect against double subscriptions
            TimeSeriesSocketHandler.subscriptions[key].add(self)
            
        #send all the data that already exists
        try:
            sensor=AssetSensor.objects.get(pk=parsedMessage['sensor'])
            recipe_instance=RecipeInstance.objects.get(pk=parsedMessage['recipe_instance'])
            data_points = TimeSeriesDataPoint.objects.filter(sensor=sensor,recipe_instance=recipe_instance)
            for data_point in data_points:
                serializer = TimeSeriesDataPointSerializer(data_point)
                self.write_message(serializer.data)
        except:
            logger.error("Error sending message", exc_info=True)
    
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
 
class RecipeInstanceHandler():
    @classmethod
    def notify(cls,brewery,recipe_instance):
        if brewery in cls.waiters:
            for waiter in cls.waiters[brewery]:
                waiter.set_result(dict(recipe_instance=recipe_instance))
        else:
            logger.warning('Brewery not in waiters')
            
    def on_connection_close(self):
        self.waiters[self.brewery].remove(self.future)
    
class RecipeInstanceStartHandler(tornado.web.RequestHandler,RecipeInstanceHandler):
    waiters = {}
    
    @gen.coroutine
    def post(self):
        logging.info("Got start watch request")
        self.brewery = Brewery.objects.get(pk=self.get_argument('brewery'))
           
        self.future = Future()
        if self.brewery.active:
            self.future.set_result(dict(recipe_instance=self.brewery.recipeinstance_set.get(active=True).pk))
        else:
            if self.brewery not in RecipeInstanceStartHandler.waiters: 
                RecipeInstanceStartHandler.waiters[self.brewery] = set()
            RecipeInstanceStartHandler.waiters[self.brewery].add(self.future)

        messages = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(dict(messages=messages))

class RecipeInstanceEndHandler(tornado.web.RequestHandler,RecipeInstanceHandler):
    waiters = {}
    
    @gen.coroutine
    def post(self):
        logging.info("Got end watch request")
        self.brewery = Brewery.objects.get(pk=self.get_argument('brewery'))
           
        self.future = Future()
        if self.brewery.active:
            if self.brewery not in RecipeInstanceEndHandler.waiters: 
                RecipeInstanceEndHandler.waiters[self.brewery] = set()
            RecipeInstanceEndHandler.waiters[self.brewery].add(self.future)

        messages = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(dict(messages=messages))
        
@receiver(post_save, sender=RecipeInstance)
def recipe_instance_watcher(sender, instance, **kwargs):
    logger.debug("Got changed recipe instance {}".format(instance))
    if instance.active:
        RecipeInstanceStartHandler.notify(instance.brewery,instance.pk)
    else:
        RecipeInstanceEndHandler.notify(instance.brewery,instance.pk)
