"""Handles websockets and asynchronous endpoints provided by Tornado instead
of Django, but use the Django model framework for a database ORM.
"""

import datetime
import logging

import tornado.escape
import tornado.web
import tornado.websocket
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token

from brewery.models import AssetSensor
from brewery.models import RecipeInstance
from brewery.models import TimeSeriesDataPoint
from brewery.serializers import TimeSeriesDataPointSerializer
from tornado_sockets.views.django import DjangoAuthenticatedWebSocketHandler

LOGGER = logging.getLogger(__name__)


class TimeSeriesSocketHandler(DjangoAuthenticatedWebSocketHandler):
    """A websocket request handler/connection used for a two-way connection
    for streaming sensor data between a client and the webserver. Allows
    for real-time streaming of sensor data as soon as it is posted.

    Client posts a subscription request, which then triggers the handler
    to send any updates to that sensor immediately to the client.

    Attributes:
        waiters: (class-level) - A set containing all of the current connection
            handlers that are active.
        subscriptions: (class-level) - A dictionary mapping to connection
            handlers. Key is specified as a tuple of (recipe_instance_pk,
            sensor_pk).
        controller_requestmap: (class-level) - A dictionary mapping a websocket
            connection to a brewhouse object. Used for indicating if a
            connection exists with a brewhouse.
        controller_controllermap: (class-level) A dictionary mapping a brewhouse
            to the websocket connection to it. Used for indicating if a
            connection exists with a brewhouse.
    """
    waiters = set()
    subscriptions = {}
    controller_requestmap = {}
    controller_controllermap = {}

    def __init__(self, *args, **kwargs):
        super(TimeSeriesSocketHandler, self).__init__(*args, **kwargs)
        self.auth = None
        self.recipe_instance_pk = None

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def _authenticate(self):
        """If the connection comes from authentication associating it with a
        particular Brewhouse, make sure we store the connection in a mapping
        between the websocket and the brewhouse.

        Stores this request in a class-level map to indicate we have an
        established connection with a Brewhouse controller.
        """
        if self.auth is not None and isinstance(self.auth, Token):
            if self.auth.brewhouse_pk:
                self.controller_controllermap[self.auth.brewhouse_pk] = self
                self.controller_requestmap[self] = self.auth.brewhouse_pk

    def _unauthenticate(self):
        """Remove this request from the class-level maps to indicate we have
        lost connection with the Brewhouse.
        """
        if self.auth is not None and isinstance(self.auth, Token):
            if self.auth.brewhouse_pk:
                del self.controller_controllermap[self.auth.brewhouse_pk]
                del self.controller_requestmap[self]

    def open(self):
        """Handles the opening of a new websocket connection for streaming data.
        """
        LOGGER.info("New websocket connection incoming %s.", self)
        self.waiters.add(self)
        self._authenticate()

    def on_close(self):
        """Handles the closing of the websocket connection, removing any
        subscriptions.
        """
        self.waiters.remove(self)
        self.unsubscribe()

        self._unauthenticate()

    def on_message(self, message):
        """Handles an incoming message in a websocket. Determines what subaction
        to route it to, and calls that sub action.

        Args:
            message: the incoming raw message from the websocket.
        """
        parsed_message = tornado.escape.json_decode(message)
        self.recipe_instance_pk = parsed_message['recipe_instance']

        if not self.check_permission():
            return

        # Subscription to a signal
        if 'subscribe' in parsed_message:
            self.subscribe(parsed_message)
        # Submission of a new datapoint
        else:
            self.new_data(parsed_message)

    def check_permission(self):
        """Checks if the user has access to the ``recipe_instance``."""
        permitted = True

        recipe_instance = RecipeInstance.objects.get(pk=self.recipe_instance_pk)

        if not permitted:
            LOGGER.error("Forbidden request %d.", recipe_instance)

        return permitted

        # TODO(willjschmitt): Get this working again.
        # user = get_current_user(self)
        # brewhouse = recipe_instance.brewhouse
        # brewery = brewhouse.brewery
        # company = brewery.company
        # has_permission = is_member_of_brewing_company(user,company)
        #
        # if not has_permission:
        #     LOGGER.error("User %s attempted to access brewhouse they do not"
        #                  " have access to (%s)",
        #                  user, recipe_instance.brewhouse)
        #
        # return has_permission

    def subscribe(self, parsed_message):
        """Handles a subscription request.

        Args:
            parsed_message: Data received from websocket.
        """
        recipe_instance_pk = parsed_message['recipe_instance']
        sensor_pk = parsed_message['sensor']

        LOGGER.debug('Subscribing')

        self._add_subscription(recipe_instance_pk, sensor_pk)

        historical_timedelta = -datetime.timedelta(minutes=15)
        self._write_historical_data(sensor_pk, recipe_instance_pk,
                                    historical_timedelta)

    def unsubscribe(self):
        for subscription in self.subscriptions.values():
            if self in subscription:
                subscription.remove(self)

    def _add_subscription(self, recipe_instance_pk, sensor_pk):
        key = (recipe_instance_pk, sensor_pk)
        if key not in self.subscriptions:
            self.subscriptions[key] = set()
        self.subscriptions[key].add(self)

    def _write_historical_data(self, sensor_pk, recipe_instance_pk, timedelta):
        """Sends all the data that already exists, limited to now + timedelta.

        Args:
            sensor_pk: The primary key for the sensor to send data.
            recipe_instance_pk: The primary key for the recipe instance to send
                data.
            timedelta: The amount of time + now to filter against for sending to
                client.
        """
        sensor = AssetSensor.objects.get(pk=sensor_pk)
        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

        now = timezone.now()
        fifteen_minutes_ago = now + timedelta
        data_points = TimeSeriesDataPoint.objects.filter(
            sensor=sensor, recipe_instance=recipe_instance,
            time__gt=fifteen_minutes_ago)
        data_points = data_points.order_by("time")
        for data_point in data_points:
            serializer = TimeSeriesDataPointSerializer(data_point)
            self.write_message(serializer.data)

    def new_data(self, parsed_message):
        """Handles a new data point request.

        Args:
            parsed_message: Data received from websocket.
        """
        LOGGER.debug('New data received.')

        data = parsed_message
        serializer = TimeSeriesDataPointSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    @classmethod
    def send_updates(cls, new_data_point):
        """Sends a new data point to all of the waiters watching the sensor it
        is associated with.

        Args:
            new_data_point: An instance of a TimeSeriesDataPoint to be streamed
                to any subscribers.
        """
        key = (new_data_point.recipe_instance.pk,new_data_point.sensor.pk)
        LOGGER.debug(str(key))
        if key in cls.subscriptions:
            waiter_count = len(cls.subscriptions[key])
            LOGGER.info("sending message to %d waiters.", waiter_count)
            for waiter in cls.subscriptions[key]:
                serializer = TimeSeriesDataPointSerializer(new_data_point)
                waiter.write_message(serializer.data)
        else:
            LOGGER.debug("No subscribers for %s.", new_data_point.sensor.name)


@receiver(post_save, sender=TimeSeriesDataPoint)
def time_series_watcher(sender, instance, **kwargs):
    """A django receiver watching for any saves on a datapoint to send
    to waiters
    """
    LOGGER.debug("Got new datapoint %s", instance)
    TimeSeriesSocketHandler.send_updates(instance)
