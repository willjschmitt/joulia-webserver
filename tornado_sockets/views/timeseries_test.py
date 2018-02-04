"""Tests for the tornado_sockets.views.timeseries module.
"""
from django.conf import settings
from django.db.models import DateTimeField
from django.db.models.fields.related import RelatedField
from django.utils import timezone
from datetime import timedelta
from tornado import gen
from tornado.escape import json_decode
from tornado.escape import json_encode
from tornado.testing import gen_test
from tornado.testing import AsyncHTTPTestCase
from tornado.websocket import websocket_connect
from unittest.mock import Mock

from brewery import models
from main import joulia_app
from testing.test import JouliaTestCase
from tornado_sockets.views import timeseries


class TestTimeSeriesSocketHandlerInternals(JouliaTestCase):
    """Tests the TimeSeriesSocketHandler internal methods."""

    def setUp(self):
        self.app = Mock()
        self.app.ui_methods = {}
        self.request = Mock()
        cookie = Mock(value="abcdefg")
        self.request.cookies = {settings.SESSION_COOKIE_NAME: cookie}
        self.request.arguments = {}
        self.request.headers = {}
        self.handler = timeseries.TimeSeriesSocketHandler(self.app,
                                                          self.request)

    def test_get_compression_options(self):
        self.assertEquals(self.handler.get_compression_options(), {})

    def test_open(self):
        self.handler.open()
        self.assertIn(self.handler, timeseries.TimeSeriesSocketHandler.waiters)

    def test_close(self):
        self.handler.waiters.add(self.handler)
        self.handler.on_close()
        self.assertNotIn(self.handler,
                         timeseries.TimeSeriesSocketHandler.waiters)

    def test_close_with_subscriptions(self):
        self.handler.waiters.add(self.handler)
        self.handler.subscriptions[(1, 1)] = {self.handler}
        self.handler.on_close()
        self.assertNotIn(self.handler,
                         timeseries.TimeSeriesSocketHandler.waiters)
        self.assertNotIn(
            self.handler,
            timeseries.TimeSeriesSocketHandler.subscriptions[(1, 1)])


class TestTimeSeriesSocketHandler(AsyncHTTPTestCase):
    """Tests the TimeSeriesSocketHandler."""

    def setUp(self):
        super(TestTimeSeriesSocketHandler, self).setUp()

        self.recipe = models.Recipe.objects.create(name="Foo")
        self.recipe_instance = models.RecipeInstance.objects.create(
            recipe=self.recipe)
        self.sensor = models.AssetSensor.objects.create()

    def get_app(self):
        return joulia_app()

    @gen.coroutine
    def generate_websocket(self, **kwargs):
        url = ("ws://localhost:" + str(self.get_http_port())
               + "/live/timeseries/socket/")
        websocket = yield websocket_connect(url, **kwargs)
        return websocket

    def deserialize(self, headers, data_list):
        result = {}
        self.assertEquals(len(headers), len(data_list))
        for i in range(len(headers)):
            result[headers[i]] = data_list[i]
        return result

    def compare_response_to_model_instance(self, response, model_instance):
        """Compares a received websocket response json string to a
        model_instance with appropriate serialization.
        """
        parsed_response = json_decode(response)
        headers = parsed_response['headers']
        data = parsed_response['data']
        self.assertEquals(len(data), len(model_instance))
        for i in range(len(data)):
            datum = self.deserialize(headers, data[i])
            self.compare_model_instance(datum, model_instance[i])

    def compare_model_instance(self, obj, model_instance):
        for key, value in obj.items():
            want = getattr(model_instance, key)
            field = model_instance._meta.get_field(key)
            if isinstance(field, RelatedField):
                self.assertEquals(value, want.pk)
            elif isinstance(field, DateTimeField):
                self.assertEquals(value, want.isoformat().replace('+00:00',
                                                                  'Z'))
            else:
                self.assertEquals(value, want)

    @gen_test
    def test_subscribe(self):
        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
        }
        websocket.write_message(json_encode(message))

    @gen_test
    def test_subscribe_with_historical_data(self):
        now = timezone.now()
        point1 = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance,
            time=now - timedelta(minutes=20))
        point2 = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance)
        point3 = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance)

        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
        }
        websocket.write_message(json_encode(message))

        response = yield websocket.read_message()
        self.compare_response_to_model_instance(
            response, [point1, point2, point3])

    @gen_test(timeout=30)
    def test_subscribe_with_historical_data_in_chunks(self):
        now = timezone.now()
        points = []
        for i in range(1001):
            now = timezone.now()
            new_point = models.TimeSeriesDataPoint.objects.create(
                sensor=self.sensor, recipe_instance=self.recipe_instance,
                time=now+timedelta(milliseconds=i))
            points.append(new_point)

        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
        }
        websocket.write_message(json_encode(message))

        response1 = yield websocket.read_message()
        self.compare_response_to_model_instance(response1, points[0:1000])
        response2 = yield websocket.read_message()
        self.compare_response_to_model_instance(response2, points[1000:])

    @gen_test
    def test_subscribe_with_historical_data_filters_based_on_time(self):
        now = timezone.now()
        # Should not see this first point in the response.
        models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance,
            time=now - timedelta(minutes=20))
        point1 = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance)
        point2 = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance)

        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
            "history_time": -15 * 60,  # Filter to only points in last 15min.
        }
        websocket.write_message(json_encode(message))

        response = yield websocket.read_message()
        self.compare_response_to_model_instance(response, [point1, point2])

    @gen_test
    def test_updated_data_received_by_subscriber(self):
        now = timezone.now()

        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
        }
        websocket.write_message(json_encode(message))

        # This sleep allows the server to finish the subscription, so it doesn't
        # treat the new datapoint as historical data.
        # TODO(willjschmitt): This will be flaky. Replace with an alternative.
        yield gen.sleep(0.02)

        new_point = models.TimeSeriesDataPoint.objects.create(
            sensor=self.sensor, recipe_instance=self.recipe_instance, time=now)

        response = yield websocket.read_message()
        self.compare_response_to_model_instance(response, [new_point])

    @gen_test(timeout=1.0)
    def test_updated_data_not_sent_to_subscriber_who_sent_it(self):
        now = timezone.now()

        # Gives a shared variable to manipulate in the closure.
        received = {'received': False}
        def message_received(*args, **kwargs):
            received['received'] = True

        websocket = yield self.generate_websocket(
            on_message_callback=message_received)

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "subscribe": True,
        }
        websocket.write_message(json_encode(message))

        # This sleep allows the server to finish the subscription, so it doesn't
        # treat the new datapoint as historical data.
        # TODO(willjschmitt): This will be flaky. Replace with an alternative.
        yield gen.sleep(0.02)

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "value": 13,
            "time": now.isoformat().replace("+00:00", "Z")
        }
        websocket.write_message(json_encode(message))

        # This sleep allows the server to finish saving the new data point to
        # the server.
        # TODO(willjschmitt): This will be flaky. Replace with an alternative
        # like a simultaneous subscription and wait for it to come in on a
        # subscribed websocket.
        yield gen.sleep(0.02)

        self.assertFalse(received['received'])

    @gen_test
    def test_new_data(self):
        count = models.TimeSeriesDataPoint.objects.filter(
            sensor=self.sensor, recipe_instance=self.recipe_instance).count()
        self.assertEquals(count, 0)

        now = timezone.now()

        websocket = yield self.generate_websocket()

        message = {
            "recipe_instance": self.recipe_instance.pk,
            "sensor": self.sensor.pk,
            "value": 13,
            "time": now.isoformat().replace("+00:00", "Z")
        }
        websocket.write_message(json_encode(message))

        # This sleep allows the server to finish saving the new data point to
        # the server.
        # TODO(willjschmitt): This will be flaky. Replace with an alternative
        # like a simultaneous subscription and wait for it to come in on a
        # subscribed websocket.
        yield gen.sleep(0.02)

        count = models.TimeSeriesDataPoint.objects.filter(
            sensor=self.sensor, recipe_instance=self.recipe_instance).count()
        self.assertEquals(count, 1)

