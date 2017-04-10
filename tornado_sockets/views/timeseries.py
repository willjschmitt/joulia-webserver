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
from tornado_sockets.views.django import DRFAuthenticationMixin

LOGGER = logging.getLogger(__name__)


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
        """Handles the opening of a new websocket connection for streaming data.

        If the connection comes from authentication associating it with a
        particular Brewhouse, make sure we store the connection in a mapping
        between the websocket and the brewhouse.
        """
        LOGGER.info("New websocket connection incomming %s", self)
        TimeSeriesSocketHandler.waiters.add(self)
        LOGGER.info("Returning %s", self)

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
        for subscription in TimeSeriesSocketHandler.subscriptions.values():
            try:
                subscription.remove(self)
            except KeyError:
                pass

        # Remove this request from the class-level maps to indicate we have lost
        # connection with the Brewhouse.
        if isinstance(getattr(self, 'auth', None), Token):
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
        LOGGER.debug('parsed message is %s', parsed_message)

        # Subscription to a signal
        if 'subscribe' in parsed_message:
            self.subscribe(parsed_message['recipe_instance'],
                           parsed_message['sensor'])
        # Submission of a new datapoint
        else:
            self.new_data(parsed_message['recipe_instance'],
                          parsed_message)

    def check_permission(self, recipe_instance):
        """Checks if the user has access to the ``recipe_instance``.

        Args:
            recipe_instance: The instance of the ``recipe_instance`` to check
                permission access for.
        """
        return True

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

    def subscribe(self, recipe_instance_pk, sensor_pk):
        """Handles a subscription request.

        Args:
            recipe_instance_pk: The primary key to the recipe instance to
                subscribe to.
            sensor_pk: The sensor primary key to subscribe to.
        """
        LOGGER.debug('Subscribing')

        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

        if not self.check_permission(recipe_instance):
            LOGGER.error("Forbidden request %d", sensor_pk)
            return

        key = (recipe_instance_pk, sensor_pk)
        LOGGER.debug(str(key))
        if key not in TimeSeriesSocketHandler.subscriptions:
            TimeSeriesSocketHandler.subscriptions[key] = set()

        # Protect against double subscriptions.
        if self not in TimeSeriesSocketHandler.subscriptions[key]:
            TimeSeriesSocketHandler.subscriptions[key].add(self)

        # Send all the data that already exists, limited to the last 15min.
        try:
            sensor = AssetSensor.objects.get(pk=sensor_pk)
            recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

            now = timezone.now()
            fifteen_minutes_ago = now - datetime.timedelta(minutes=15)
            data_points = TimeSeriesDataPoint.objects.filter(
                sensor=sensor, recipe_instance=recipe_instance,
                time__gt=fifteen_minutes_ago)
            data_points = data_points.order_by("time")
            for data_point in data_points:
                serializer = TimeSeriesDataPointSerializer(data_point)
                self.write_message(serializer.data)
        except:
            LOGGER.error("Error sending message", exc_info=True)

    def new_data(self, recipe_instance_pk, data):
        """Handles a new data point request.

        Args:
            recipe_instance_pk: The primary key to the recipe instance to
                subscribe to.
            data: The data for a new data point.
        """
        LOGGER.debug('New data received.')

        recipe_instance = RecipeInstance.objects.get(pk=recipe_instance_pk)

        if not self.check_permission(recipe_instance):
            LOGGER.error("Forbidden request %s", data)
            return

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
            LOGGER.info("sending message to %d waiters",
                        len(cls.subscriptions[key]))
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
    LOGGER.debug("Got new datapoint %s", instance)
    TimeSeriesSocketHandler.send_updates(instance)
