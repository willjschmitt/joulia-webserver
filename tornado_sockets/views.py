'''Handles websockets and asynchronous endpoints provided by Tornado instead
of Django, but use the Django model framework for a database ORM.
'''
import datetime
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.settings import api_settings
from tornado import gen
from tornado.concurrent import Future
import tornado.escape
import tornado.web
import tornado.websocket

from brewery.models import AssetSensor
from brewery.models import Brewhouse
from brewery.models import RecipeInstance
from brewery.models import TimeSeriesDataPoint
from brewery.permissions import is_member_of_brewing_company
from brewery.serializers import TimeSeriesDataPointSerializer

from .utils import get_current_user


LOGGER = logging.getLogger(__name__)

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
    def _request(self):
        return self


class TimeSeriesSocketHandler(DRFAuthenticationMixin,
                              tornado.websocket.WebSocketHandler):
    """A websocket request handler/connection used for a two-way connection
    for streaming sensor data between a client and the webserver. Allows
    for real-time streaming of sensor data as soon as it is posted.

    Client posts a subscription request, which then triggers the handler
    to send any updates to that sensor immediately to the client.

    Attributes:
        waiters: (class-level) - A set containing all of the current
            connection handlers that are active.
        subscriptions: (class-level) - A dictionary mapping to
            connection handlers. Key is specified as a tuple of
            (recipe_instance_pk,sensor_pk).
        controller_requestmap: (class-level) - A dictionary mapping a
            websocket connection to a brewhouse object. Used for
            indicating if a connection exists with a brewhouse.
        controller_controllermap: (class-level) A dictionary mapping
            a brewhouse to the websocket connection to it. Used for
            indicating if a connection exists with a brewhouse.
    """
    waiters = set()
    subscriptions = {}
    controller_requestmap = {}
    controller_controllermap = {}

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        '''Handles the opening of a new websocket connection for streaming
        data.

        If the connection comes from authentication associating it with a
        particular Brewhouse, make sure we store the connection in a
        mapping between the websocket and the brewhouse'''
        LOGGER.info("New websocket connection incomming %s",self)
        TimeSeriesSocketHandler.waiters.add(self)
        LOGGER.info("Returning %s",self)

        # Store this request in a class-level map to indicate we have an
        # established connection with a Brewhouse controller.
        if isinstance(getattr(self,'auth',None),Token):
            if self.auth.brewhouse:
                self.controller_controllermap[self.auth.brewhouse] = self
                self.controller_requestmap[self] = self.auth.brewhouse

    def on_close(self):
        """Handles the closing of the websocket connection, removing any
        subscriptions.
        """
        TimeSeriesSocketHandler.waiters.remove(self)
        for subscription in TimeSeriesSocketHandler.subscriptions.itervalues():
            try:
                subscription.remove(self)
            except KeyError:
                pass

        # Remove this request from the class-level maps to indicate we have
        # lost connection with the Brewhouse.
        if isinstance(getattr(self,'auth',None),Token):
            if self.auth.brewhouse:
                del self.controller_controllermap[self.auth.brewhouse]
                del self.controller_requestmap[self]

    def on_message(self, message):
        """Handles an incoming message in a websocket. Determines what
        subaction to route it to, and calls that sub action.

        Args:
            message: the incoming raw message from the websocket
        """
        parsed_message = tornado.escape.json_decode(message)
        LOGGER.debug('parsed message is %s',parsed_message)

        # Subscription to a signal
        if 'subscribe' in parsed_message:
            self.subscribe(parsed_message['recipe_instance'],
                           parsed_message['sensor'])
        # Submission of a new datapoint
        else:
            self.new_data(parsed_message['recipe_instance'],
                          parsed_message)

    def check_permission(self,recipe_instance):
        """Checks if the user has access to the ``recipe_instance``.

        Args:
            recipe_instance: The instance of the ``recipe_instance`` to
                check permission access for.
        """
        return True
        user = get_current_user(self)
        brewhouse = recipe_instance.brewhouse
        brewery = brewhouse.brewery
        company = brewery.company
        has_permission =  is_member_of_brewing_company(user,company)

        if not has_permission:
            LOGGER.error("User %s attempted to access brewhouse they do not"
                         " have access to (%s)",
                         user,recipe_instance.brewhouse)

        return has_permission

    def subscribe(self,recipe_instance_pk,sensor_pk):
        """Handles a subscription request.

        Args:
            recipe_instance_pk: The primary key to the recipe instance to
                subscribe to.
            sensor_pk: The sensor primary key to subscribe to
        """
        LOGGER.debug('Subscribing')

        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

        if not self.check_permission(recipe_instance):
            LOGGER.error("Forbidden request %d",sensor_pk)
            return

        key = (recipe_instance_pk,sensor_pk)
        LOGGER.debug(str(key))
        if key not in TimeSeriesSocketHandler.subscriptions:
            TimeSeriesSocketHandler.subscriptions[key] = set()

        # Protect against double subscriptions
        if self not in TimeSeriesSocketHandler.subscriptions[key]:
            TimeSeriesSocketHandler.subscriptions[key].add(self)

        # Send all the data that already exists, limited to the last 15min
        try:
            sensor=AssetSensor.objects.get(pk=sensor_pk)
            recipe_instance=RecipeInstance.objects.get(pk=recipe_instance_pk)

            now = timezone.now()
            fiftteen_minutes_ago = now - datetime.timedelta(minutes=15)
            data_points = TimeSeriesDataPoint.objects.filter(sensor=sensor,
                                                             recipe_instance=recipe_instance,
                                                             time__gt=fiftteen_minutes_ago)
            data_points = data_points.order_by("time")
            for data_point in data_points:
                serializer = TimeSeriesDataPointSerializer(data_point)
                self.write_message(serializer.data)
        except:
            LOGGER.error("Error sending message", exc_info=True)

    def new_data(self,recipe_instance_pk,data):
        """Handles a new data point request.

        Args:
            recipe_instance_pk: The primary key to the recipe instance to
                subscribe to.
            data: The data for a new data point.
        """
        LOGGER.debug('New data recieved')

        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

        if not self.check_permission(recipe_instance):
            LOGGER.error("Forbidden request %s",data)
            return

        serializer = TimeSeriesDataPointSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    @classmethod
    def send_updates(cls, new_data_point):
        """Sends a new data point to all of the waiters watching the
        sensor it is associated with.

        Args:
            new_data_point: An instance of a TimeSeriesDataPoint to be
                streamed to any subscribers.
        """
        key = (new_data_point.recipe_instance.pk,new_data_point.sensor.pk)
        LOGGER.debug(str(key))
        if key in cls.subscriptions:
            LOGGER.info("sending message to %d waiters", len(cls.subscriptions[key]))
            for waiter in cls.subscriptions[key]:
                try:
                    serializer = TimeSeriesDataPointSerializer(new_data_point)
                    data = serializer.data
                    data['name'] = new_data_point.sensor.name
                    waiter.write_message(data)
                except:
                    LOGGER.error("Error sending message", exc_info=True)
        else:
            LOGGER.debug("No subscribers for %s", new_data_point.sensor.name)

@receiver(post_save, sender=TimeSeriesDataPoint)
def time_series_watcher(sender, instance, **kwargs):
    """A django receiver watching for any saves on a datapoint to send
    to waiters
    """
    LOGGER.debug("Got new datapoint %s",instance)
    TimeSeriesSocketHandler.send_updates(instance)


class RecipeInstanceHandler(tornado.web.RequestHandler):
    """A base handler for the start and end for a recipe instance. Is
    abstract, and meant to serve as commonality for the start and finish
    of a brewing event (``RecipeInstance``).

    Attributes:
        brewhouse: the brewhouse being waited on in this http request.
            Must be set in child class implementation.
        future: the tornado ``future`` being waited on in this http request.
            Must be set in child class implementation.
    """

    def __init__(self,*args,**kwargs):
        super(RecipeInstanceHandler,self).__init__(*args,**kwargs)
        self.brewhouse = None
        self.future = None

    def post(self,*args,**kwargs):
        """The post handler, which should be set by the child class in
        order to handle the start/end requests.
        """
        raise NotImplementedError()

    @property
    def waiters(self):
        """A dictionary to map a brewhouse to a long polled request
        waiting for a change in the active status of a brewhouse.
        """
        raise NotImplementedError("`waiters` class attribute must be"
                                  " established for child class.")

    @classmethod
    def notify(cls,brewhouse,recipe_instance):
        """Notifies any waiters for the given brewhouse with the
        ``recipe_instance``.

        Args:
            brewhouse: The brewhouse primary key to notify.
            recipe_instance: The recipe_instance primary key to send
                to waiters on the brewhouse.
        """
        if brewhouse in cls.waiters:
            for waiter in cls.waiters[brewhouse]:
                waiter.set_result(dict(recipe_instance=recipe_instance))
        else:
            LOGGER.warning('Brewhouse not in waiters')

    def on_connection_close(self):
        self.waiters[self.brewhouse].remove(self.future)

    def has_permission(self,brewhouse):
        """Checks if the currently authenticated user has access to the
        ``brewhouse``.

        Args:
            brewhouse: The ``Brewhouse`` instance to check permissions
                against
        """
        brewery = brewhouse.brewery
        brewing_company = brewery.company
        if not is_member_of_brewing_company(self.current_user,brewing_company):
            self.set_status(status.HTTP_403_FORBIDDEN,
                            'Must be member of brewing company.')
            return False

        return True


class RecipeInstanceStartHandler(DRFAuthenticationMixin,
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
        LOGGER.info("Got start watch request")
        brewhouse_id = self.get_argument('brewhouse')
        self.brewhouse = Brewhouse.objects.get(pk=brewhouse_id)

        #check permission
        if not self.has_permission(self.brewhouse):
            return

        self.future = Future()
        if self.brewhouse.active:
            recipe_instance = self.brewhouse.active_recipe_instance
            self.future.set_result({"recipe_instance":recipe_instance.pk})
        else:
            if self.brewhouse not in RecipeInstanceStartHandler.waiters:
                RecipeInstanceStartHandler.waiters[self.brewhouse] = set()
            RecipeInstanceStartHandler.waiters[self.brewhouse].add(self.future)

        messages = yield self.future
        if self.request.connection.stream.closed():
            LOGGER.debug('Lost waiter connection')
            RecipeInstanceStartHandler.waiters[self.brewhouse].remove(self.future)
            return
        self.write(dict(messages=messages))

        return


class RecipeInstanceEndHandler(DRFAuthenticationMixin,
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
        LOGGER.info("Got end watch request")
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
            LOGGER.debug('Lost waiter connection')
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
    RecipeInstanceStartHandler notify classmethod.

    If a RecipeInstance is saved and now inactive, the
    RecipeInstanceEndHandler notify classmethod.
    '''
    LOGGER.debug("Got changed recipe instance %s",instance)
    if instance.active:
        RecipeInstanceStartHandler.notify(instance.brewhouse,instance.pk)
    else:
        RecipeInstanceEndHandler.notify(instance.brewhouse,instance.pk)
