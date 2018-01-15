"""Handles asynchronous long polling endpoints for start/stop of
RecipeInstance's.
"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from tornado import gen
from tornado.concurrent import Future

from brewery.models import Brewhouse, RecipeInstance
from brewery.permissions import is_member_of_brewing_company
from tornado_sockets.views.django import DjangoAuthenticatedRequestHandler

LOGGER = logging.getLogger(__name__)


class RecipeInstanceHandler(DjangoAuthenticatedRequestHandler):
    """A base handler for the start and end for a recipe instance. Is abstract,
    and meant to serve as commonality for the start and finish of a brewing
    event (``RecipeInstance``).

    Attributes:
        brewhouse: the brewhouse being waited on in this http request. Must be
            set in child class implementation.
        future: the tornado ``future`` being waited on in this http request.
            Must be set in child class implementation.
        waiters: A dictionary to map a brewhouse to a long polled request
            waiting for a change in the active status of a brewhouse.
    """
    # Subclasses should create their own of this, since the mutability will be
    # otherwise shared between all classes.
    waiters = {}

    def __init__(self, *args, **kwargs):
        super(RecipeInstanceHandler, self).__init__(*args, **kwargs)
        self.brewhouse = None
        self.future = None

    @gen.coroutine
    def post(self):
        """The POST request to handle the recipe end watch.

        Args:
            brewhouse: POST argument with the ID for the brewhouse to watch for
                an ended recipe instance.

        Raises:
            403_FORBIDDEN response: if user is not authorized to access
                brewhouse through brewing company association.
            404_NOT_FOUND response: if the requested brewhouse does not exist.

        Returns:
            A yielded waiter attached to class object to receive update when the
            yield is returned.
        """
        ok_to_proceed = self.get_and_check_permission()
        if not ok_to_proceed:
            return

        self.future = Future()
        self.register_waiter()
        self.handle_request()
        result = yield self.future

        if self.request.connection.stream.closed():
            self._handle_lost_connection()
            return

        self.write(result)
        self.unregister_waiter()

    def handle_request(self):
        """Handles the particulars for start/stopping an instance. Should be
        implemented by child class.
        """
        raise NotImplementedError()

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
            LOGGER.warning('Brewhouse %s not in waiters', brewhouse)

    def on_connection_close(self):
        self._handle_lost_connection()

    def has_permission(self, brewhouse):
        """Checks if the currently authenticated user has access to the
        ``brewhouse``.

        Args:
            brewhouse: The ``Brewhouse`` instance to check permissions against.
        """
        try:
            brewing_company = brewhouse.brewery.company
        # In case brewery or company is not assigned to brewhouse.
        except AttributeError:
            permission = False
        else:
            permission = is_member_of_brewing_company(
                self.current_user, brewing_company)

        if not permission:
            message = (
                'Must be member of brewing company to watch brewhouse {}.'
                .format(brewhouse))
            LOGGER.error(message)
            self.set_status(status.HTTP_403_FORBIDDEN, message)

        return permission

    def get_brewhouse(self):
        """Attempts to set `brewhouse` attribute based on the provided argument.
        If not found, sets the status as a 404 and returns False. If found,
        returns True and sets `brewhouse`."""
        brewhouse_pk = self.get_body_argument('brewhouse')
        try:
            self.brewhouse = Brewhouse.objects.get(pk=brewhouse_pk)
        except ObjectDoesNotExist:
            message = 'Brewhouse {} not found.'.format(brewhouse_pk)
            self.set_status(status.HTTP_404_NOT_FOUND, message)
            LOGGER.error(message)
            return False
        else:
            return True

    def register_waiter(self):
        """Registers the currently set future as a waiter for the brewhouse."""
        if self.brewhouse not in self.waiters:
            # TODO(willjschmitt): Consider making set into weakref set so the
            # futures in it can disappear from the class variable in case the
            # instance goes away.
            self.waiters[self.brewhouse] = set()
        self.waiters[self.brewhouse].add(self.future)

    def unregister_waiter(self):
        """Unregisters the currenty set future. Useful when connection is lost,
        or the request has been fulfilled.
        """
        if self.brewhouse in self.waiters:
            waiter = self.waiters[self.brewhouse]
            waiter.remove(self.future)

    def _handle_lost_connection(self):
        """Removes current future for brewhouse."""
        LOGGER.debug('Lost waiter connection for %s.', self.brewhouse)
        self.unregister_waiter()

    def get_and_check_permission(self):
        """Gets the brewhouse and checks permission. If any step fails, returns
        False, otherwise returns True.
        """
        brewhouse_found = self.get_brewhouse()
        if not brewhouse_found:
            return False

        if not self.has_permission(self.brewhouse):
            return False

        return True


class RecipeInstanceStartHandler(RecipeInstanceHandler):
    """A long-polling request to monitor a brewhouse until it has a recipe
    launched. If a recipe instance is already launched on it, the request is
    immediately fulfilled. If the brewhouse is not launched, the request returns
    once the brewhouse has a recipe launched. The returned result includes the
    active recipe instance keyed on "recipe_instance".
    """
    waiters = {}

    def handle_request(self):
        LOGGER.info("Got start watch request for brewhouse %s.", self.brewhouse)
        if self.brewhouse.active:
            recipe_instance = self.brewhouse.active_recipe_instance
            LOGGER.info("System already active. Immediately returning %s.",
                        recipe_instance)
            self.future.set_result({"recipe_instance": recipe_instance.pk})


class RecipeInstanceEndHandler(RecipeInstanceHandler):
    """A long-polling request to wait for a recipe instance to be ended for a
    Brewhouse. If a brewhouse does not have any active recipe instance, the
    request is immediately fulfilled. If the brewhouse has an active recipe
    instance, the request returns once the brewhouse is requested to end its
    instance. The request returns the recipe_instance in the response keyed on
    itself if one was active while waiting. If there was no instance active on
    request, returns None for the recipe_instance.
    """
    waiters = {}

    def handle_request(self):
        LOGGER.info("Got end watch request for brewhouse %s.", self.brewhouse)
        if not self.brewhouse.active:
            LOGGER.info("System already inactive. Immediately returning.")
            self.future.set_result({"recipe_instance": None})


@receiver(post_save, sender=RecipeInstance)
def recipe_instance_watcher(sender, instance, **kwargs):
    """Django receiver to watch for changes made to RecipeInstances and sends
    notifications to the waiters in the RecipeInstanceStart/EndHandler's.

    If a RecipeInstance is saved and now active, the RecipeInstanceStartHandler
    notify classmethod.

    If a RecipeInstance is saved and now inactive, the RecipeInstanceEndHandler
    notify classmethod.
    """
    LOGGER.debug("Observed changed recipe instance: %s.", instance)
    if instance.active:
        RecipeInstanceStartHandler.notify(instance.brewhouse, instance.pk)
    else:
        RecipeInstanceEndHandler.notify(instance.brewhouse, instance.pk)
