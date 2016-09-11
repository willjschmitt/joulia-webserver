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

from rest_framework.settings import api_settings
from rest_framework import status
from rest_framework.authtoken.models import Token

from brewery.models import Brewhouse
from brewery.models import RecipeInstance
from brewery.models import AssetSensor
from brewery.models import TimeSeriesDataPoint
from brewery.serializers import TimeSeriesDataPointSerializer
from brewery.permissions import is_member_of_brewing_company

from .utils import get_current_user

import logging
logger = logging.getLogger(__name__)

class DRFAuthenticationMixin(object):
    '''Uses the django rest framework authentication handlers for the
    Tornado handlers, which are all asynchronous and done through XHR
    or other API-like operations rather than browser page requests.
    '''
    
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    def get_current_user(self):
        '''Gets the current user using the django rest framework
        `authentication_classes`. The classes default to those
        from the settings, but can always be overridden in child
        classes.
        '''
        authenticators = (auth() for auth in self.authentication_classes)
        self.auth = None
        for authenticator in authenticators:
            try:
                user_auth_tuple = authenticator.authenticate(self)
            except:
                pass

            if user_auth_tuple is not None:
                self._authenticator = authenticator
                user = user_auth_tuple[0]
                self.auth = user_auth_tuple[1]
                return user
    
    @property
    def META(self):
        '''Mocks a conversion of the tornado headers into django
        headers, since tornado doesn't have really middleware that
        manipulates the incoming headers. Particularly, this function
        takes the "Authorization" header incoming from tornado and
        returns a dictionary with "HTTP_AUTHORIZATION" containing the
        same value'''
        tornado_auth_header = self.request.headers['Authorization']
        headers = {'HTTP_AUTHORIZATION':tornado_auth_header}
        return headers
    
    @property
    def _request(self): return self
    
class TimeSeriesSocketHandler(DRFAuthenticationMixin,
                              tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200
    
    subscriptions = {}
    
    # These class-level attributes store a map of requests to Brewhouse
    # controllers whenever a controller establishes a websocket connection
    controller_requestmap = {}
    controller_controllermap = {}

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    '''
    Core websocket functions
    '''
    def open(self):
        '''Handles the opening of a new websocket connection for streaming
        data.
        
        If the connection comes from authentication associating it with a
        particular Brewhouse, make sure we store the connection in a
        mapping between the websocket and the brewhouse'''
        
        logger.info("New websocket connection incomming {}".format(self))
        TimeSeriesSocketHandler.waiters.add(self)
        logger.info("returning {}".format(self))
        
        # Store this request in a class-level map to indicate we have an
        # established connection with a Brewhouse controller.
        if isinstance(getattr(self,'auth',None),Token):
            if self.auth.brewhouse:
                self.controller_controllermap[self.auth.brewhouse] = self
                self.controller_requestmap[self] = self.auth.brewhouse

    def on_close(self):
        TimeSeriesSocketHandler.waiters.remove(self)
        for subscription in TimeSeriesSocketHandler.subscriptions.itervalues():
            try: subscription.remove(self)
            except KeyError: pass
            
        # Remove this request from the class-level maps to indicate we have
        # lost connection with the Brewhouse.
        if isinstance(getattr(self,'auth',None),Token):
            if self.auth.brewhouse:
                del self.controller_controllermap[self.auth.brewhouse]
                del self.controller_requestmap[self]
            
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
        brewhouse = recipe_instance.brewhouse
        brewery = brewhouse.brewery
        if not is_member_of_brewing_company(user,brewery):
            logger.error("User {} attempted to access brewhouse "
                         "they do not have access to ({})"
                         "".format(user,recipe_instance.brewhouse))
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
            data_points = TimeSeriesDataPoint.objects.filter(sensor=sensor,
                                                             recipe_instance=recipe_instance)
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
    def notify(cls,brewhouse,recipe_instance):
        if brewhouse in cls.waiters:
            for waiter in cls.waiters[brewhouse]:
                waiter.set_result(dict(recipe_instance=recipe_instance))
        else:
            logger.warning('Brewhouse not in waiters')
            
    def on_connection_close(self):
        self.waiters[self.brewhouse].remove(self.future)
        
    def has_permission(self,brewhouse):
        #check permission
        brewery = brewhouse.brewery
        brewing_company = brewery.company
        if not is_member_of_brewing_company(self.current_user,brewing_company):
            self.set_status(status.HTTP_403_FORBIDDEN,
                            'Must be member of brewing company.')
            return False
        
        return True
    
class RecipeInstanceStartHandler(DRFAuthenticationMixin,
                                 tornado.web.RequestHandler,
                                 RecipeInstanceHandler):
    '''A long-polling request to see if a brewhouse has a recipe
    launched. If a brewhouse is already launched, the request is
    immediately fulfilled. If the brewhouse is not launched,
    the request returns once the brewhouse has a recipe launched.'''
    waiters = {}
    
    @gen.coroutine
    def post(self):
        '''The POST request to handle the recipe start watch.
        
        Args:
            brewhouse: POST argument with the ID for the brewhouse
                to watch for a started recipe instance
        
        Raises:
            403_FORBIDDEN response: if user is not authorized to access
                brewhouse through brewing company association
        
        Returns:
            A yielded waiter attached to class object to receive update
                when the yield is returned.
        '''
        logger.info("Got start watch request")
        brewhouse_id = self.get_argument('brewhouse')
        self.brewhouse = Brewhouse.objects.get(pk=brewhouse_id)
        
        #check permission
        if not self.has_permission(self.brewhouse):
            return
        
        self.future = Future()
        if self.brewhouse.active:
            recipe_instance = self.brewhouse.active_recipe_instance
            self.future.set_result({recipe_instance:recipe_instance.pk})
        else:
            if self.brewhouse not in RecipeInstanceStartHandler.waiters: 
                RecipeInstanceStartHandler.waiters[self.brewhouse] = set()
            RecipeInstanceStartHandler.waiters[self.brewhouse].add(self.future)
        
        messages = yield self.future
        if self.request.connection.stream.closed():
            logger.debug('Lost waiter connection')
            RecipeInstanceStartHandler.waiters[self.brewhouse].remove(self.future)
            return
        self.write(dict(messages=messages))
        
        return

class RecipeInstanceEndHandler(DRFAuthenticationMixin,
                               tornado.web.RequestHandler,
                               RecipeInstanceHandler):
    '''A long-polling request to wait for a recipe instance to be
    ended for a Brewhouse. If a brewhouse does not have any active
    recipe instance, the request is immediately fulfilled. 
    If the brewhouse is launched, the request returns once the 
    brewhouse is requested to end it's instance.'''
    waiters = {}
    
    @gen.coroutine
    def post(self):
        '''The POST request to handle the recipe end watch.
        
        Args:
            brewhouse: POST argument with the ID for the brewhouse
                to watch for an ended recipe instance
        
        Raises:
            403_FORBIDDEN response: if user is not authorized to access
                brewhouse through brewing company association
        
        Returns:
            A yielded waiter attached to class object to receive update
                when the yield is returned.
        '''
        logger.info("Got end watch request")
        self.brewhouse = Brewhouse.objects.get(pk=self.get_argument('brewhouse'))
        
        #check permission
        if not self.has_permission(self.brewhouse):
            return
        
        self.future = Future()
        if self.brewhouse.active:
            if self.brewhouse not in RecipeInstanceEndHandler.waiters: 
                RecipeInstanceEndHandler.waiters[self.brewhouse] = set()
            RecipeInstanceEndHandler.waiters[self.brewhouse].add(self.future)

        messages = yield self.future
        if self.request.connection.stream.closed():
            logger.debug('Lost waiter connection')
            RecipeInstanceEndHandler.waiters[self.brewhouse].remove(self.future)
            return
        self.write(dict(messages=messages))
        
        return
        
@receiver(post_save, sender=RecipeInstance)
def recipe_instance_watcher(sender, instance, **kwargs):
    '''Django receiver to watch for changes made to RecipeInstances
    and sends notifications to the waiters in the 
    RecipeInstanceStart/EndHandler's.
    
    If a RecipeInstance is saved and now active, the 
    RecipeInstanceStartHandler nofify classmethod.
    
    If a RecipeInstance is saved and now inactive, the 
    RecipeInstanceEndHandler nofify classmethod.
    '''
    logger.debug("Got changed recipe instance {}".format(instance))
    if instance.active:
        RecipeInstanceStartHandler.notify(instance.brewhouse,instance.pk)
    else:
        RecipeInstanceEndHandler.notify(instance.brewhouse,instance.pk)
