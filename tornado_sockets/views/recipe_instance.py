"""Handles asynchronous long polling endpoints for start/stop of
RecipeInstance's.
"""

import tornado.web
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from tornado import gen
from tornado.concurrent import Future

from brewery.models import Brewhouse, RecipeInstance
from brewery.permissions import is_member_of_brewing_company
from tornado_sockets.views.timeseries import LOGGER
from tornado_sockets.views.django import DRFAuthenticationMixin


class RecipeInstanceHandler(tornado.web.RequestHandler):
    """A base handler for the start and end for a recipe instance. Is abstract,
    and meant to serve as commonality for the start and finish of a brewing
    event (``RecipeInstance``).

    Attributes:
        brewhouse: the brewhouse being waited on in this http request. Must be
            set in child class implementation.
        future: the tornado ``future`` being waited on in this http request.
            Must be set in child class implementation.
    """

    def __init__(self, *args, **kwargs):
        super(RecipeInstanceHandler, self).__init__(*args, **kwargs)
        self.brewhouse = None
        self.future = None

    def post(self, *args, **kwargs):
        """The post handler, which should be set by the child class in
        order to handle the start/end requests.
        """
        raise NotImplementedError()

    @property
    def waiters(self):
        """A dictionary to map a brewhouse to a long polled request
        waiting for a change in the active status of a brewhouse.
        """
        raise NotImplementedError(
            "`waiters` class attribute must be established for child class.")

    @classmethod
    def notify(cls, brewhouse, recipe_instance):
        """Notifies any waiters for the given brewhouse with the
        ``recipe_instance``.

        Args:
            brewhouse: The brewhouse primary key to notify.
            recipe_instance: The recipe_instance primary key to send to waiters
                on the brewhouse.
        """
        if brewhouse in cls.waiters:
            for waiter in cls.waiters[brewhouse]:
                waiter.set_result(dict(recipe_instance=recipe_instance))
        else:
            LOGGER.warning('Brewhouse not in waiters')

    def on_connection_close(self):
        self.waiters[self.brewhouse].remove(self.future)

    def has_permission(self, brewhouse):
        """Checks if the currently authenticated user has access to the
        ``brewhouse``.

        Args:
            brewhouse: The ``Brewhouse`` instance to check permissions
                against
        """
        brewery = brewhouse.brewery
        brewing_company = brewery.company
        if not is_member_of_brewing_company(self.current_user, brewing_company):
            self.set_status(status.HTTP_403_FORBIDDEN,
                            'Must be member of brewing company.')
            return False

        return True


class RecipeInstanceStartHandler(DRFAuthenticationMixin, RecipeInstanceHandler):
    """A long-polling request to see if a brewhouse has a recipe launched. If a
    brewhouse is already launched, the request is immediately fulfilled. If the
    brewhouse is not launched, the request returns once the brewhouse has a
    recipe launched.
    """
    waiters = {}

    @gen.coroutine
    def post(self):
        """The POST request to handle the recipe start watch.

        Args:
            brewhouse: POST argument with the ID for the brewhouse to watch for
                a started recipe instance.

        Raises:
            403_FORBIDDEN response: if user is not authorized to access
                brewhouse through brewing company association.

        Returns:
            A yielded waiter attached to class object to receive update when the
            yield is returned.
        """
        LOGGER.info("Got start watch request")
        brewhouse_id = self.get_argument('brewhouse')
        self.brewhouse = Brewhouse.objects.get(pk=brewhouse_id)

        if not self.has_permission(self.brewhouse):
            return

        self.future = Future()
        if self.brewhouse.active:
            recipe_instance = self.brewhouse.active_recipe_instance
            self.future.set_result({"recipe_instance": recipe_instance.pk})
        else:
            if self.brewhouse not in RecipeInstanceStartHandler.waiters:
                RecipeInstanceStartHandler.waiters[self.brewhouse] = set()
            RecipeInstanceStartHandler.waiters[self.brewhouse].add(self.future)

        messages = yield self.future
        if self.request.connection.stream.closed():
            LOGGER.debug('Lost waiter connection')
            waiter = RecipeInstanceStartHandler.waiters[self.brewhouse]
            waiter.remove(self.future)
            return
        self.write(dict(messages=messages))

        return


class RecipeInstanceEndHandler(DRFAuthenticationMixin, RecipeInstanceHandler):
    """A long-polling request to wait for a recipe instance to be ended for a
    Brewhouse. If a brewhouse does not have any active recipe instance, the
    request is immediately fulfilled. If the brewhouse is launched, the request
    returns once the brewhouse is requested to end its instance.
    """
    waiters = {}

    @gen.coroutine
    def post(self):
        """The POST request to handle the recipe end watch.

        Args:
            brewhouse: POST argument with the ID for the brewhouse to watch for
                an ended recipe instance.

        Raises:
            403_FORBIDDEN response: if user is not authorized to access
                brewhouse through brewing company association.

        Returns:
            A yielded waiter attached to class object to receive update when the
            yield is returned.
        """
        LOGGER.info("Got end watch request.")
        self.brewhouse = Brewhouse.objects.get(
            pk=self.get_argument('brewhouse'))

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
    """Django receiver to watch for changes made to RecipeInstances and sends
    notifications to the waiters in the RecipeInstanceStart/EndHandler's.

    If a RecipeInstance is saved and now active, the RecipeInstanceStartHandler
    notify classmethod.

    If a RecipeInstance is saved and now inactive, the RecipeInstanceEndHandler
    notify classmethod.
    """
    LOGGER.debug("Got changed recipe instance %s", instance)
    if instance.active:
        RecipeInstanceStartHandler.notify(instance.brewhouse, instance.pk)
    else:
        RecipeInstanceEndHandler.notify(instance.brewhouse, instance.pk)