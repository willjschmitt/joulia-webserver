"""Test for the tornado_sockets.views.recipe_instance module."""

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from rest_framework import status
from tornado import gen
from tornado.concurrent import Future
from tornado.escape import utf8
from tornado.ioloop import IOLoop
from unittest.mock import MagicMock

from brewery.models import Brewery
from brewery.models import Brewhouse
from brewery.models import BrewingCompany
from brewery.models import Recipe
from brewery.models import RecipeInstance
from testing.test import JouliaTestCase
from tornado_sockets.views import recipe_instance


class TestRecipeInstanceHandler(JouliaTestCase):
    """Tests for the RecipeInstanceHandler class."""

    def setUp(self):
        super(TestRecipeInstanceHandler, self).setUp()
        self.handler = recipe_instance.RecipeInstanceHandler(self.app,
                                                             self.request)

    def test_post_success(self):
        class RecipeInstanceHandlerImplementer(
                recipe_instance.RecipeInstanceHandler):
            waiters = {}

            def handle_request(self):
                self.future.set_result({"fake": "result"})

        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)
        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)

        handler = RecipeInstanceHandlerImplementer(self.app, self.request)
        handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        handler.request.connection.stream.closed = MagicMock(return_value=False)
        IOLoop.current().run_sync(handler.post)
        self.assertEquals(handler._status_code, status.HTTP_200_OK)
        self.assertIn(b'{"fake": "result"}', handler._write_buffer)

    def test_post_poller_disconnects(self):
        class RecipeInstanceHandlerImplementer(
                recipe_instance.RecipeInstanceHandler):
            waiters = {}

            def handle_request(self):
                self.future.set_result({"fake": "result"})

        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)
        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)

        handler = RecipeInstanceHandlerImplementer(self.app, self.request)
        handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        handler.request.connection.stream.closed = MagicMock(return_value=True)
        IOLoop.current().run_sync(handler.post)
        self.assertEquals(handler._status_code, status.HTTP_200_OK)
        self.assertEquals(handler._write_buffer, [])

    def test_post_no_auth_not_ok_to_proceed(self):
        class RecipeInstanceHandlerImplementer(
                recipe_instance.RecipeInstanceHandler):
            waiters = {}

            def handle_request(self):
                self.future.set_result({"fake": "result"})

        brewhouse = Brewhouse.objects.create(name="Bar")

        handler = RecipeInstanceHandlerImplementer(self.app, self.request)
        handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        handler.request.connection.stream.closed = MagicMock(return_value=False)
        IOLoop.current().run_sync(handler.post)
        self.assertEquals(handler._write_buffer, [])

    def test_handle_request(self):
        with self.assertRaises(NotImplementedError):
            self.handler.handle_request()

    def test_notify_not_in_waiters(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        recipe = Recipe.objects.create(name="Bar")
        instance = RecipeInstance.objects.create(recipe=recipe)
        recipe_instance.RecipeInstanceHandler.notify(brewhouse.pk, instance.pk)

    def test_notify_waiter(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        recipe = Recipe.objects.create(name="Bar")
        instance = RecipeInstance.objects.create(recipe=recipe)
        future = Future()
        recipe_instance.RecipeInstanceHandler.waiters[brewhouse.pk] = [future]
        recipe_instance.RecipeInstanceHandler.notify(brewhouse.pk, instance.pk)
        self.assertEquals(future.result(), {'recipe_instance': instance.pk})

    def test_notify_waiter_only_correct_brewhouse(self):
        brewhouse1 = Brewhouse.objects.create(name="Foo")
        brewhouse2 = Brewhouse.objects.create(name="Baz")
        recipe = Recipe.objects.create(name="Bar")
        instance = RecipeInstance.objects.create(recipe=recipe)
        future1 = Future()
        future2 = Future()
        recipe_instance.RecipeInstanceHandler.waiters[brewhouse1.pk] = [future1]
        recipe_instance.RecipeInstanceHandler.waiters[brewhouse2.pk] = [future2]
        recipe_instance.RecipeInstanceHandler.notify(brewhouse1.pk, instance.pk)
        self.assertEquals(future1.result(), {'recipe_instance': instance.pk})
        self.assertFalse(future2.done())

    def test_on_connection_close_removes_waiter(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        future = Future()
        recipe_instance.RecipeInstanceHandler.waiters[brewhouse.pk] = [future]
        self.handler.brewhouse = brewhouse.pk
        self.handler.future = future
        self.handler.on_connection_close()

        self.assertEquals(
            recipe_instance.RecipeInstanceHandler.waiters[brewhouse.pk], [])

    def test_has_permission_is_member(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)
        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        self.assertTrue(self.handler.has_permission(brewhouse))

    def test_has_permission_is_not_member(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        self.assertFalse(self.handler.has_permission(brewhouse))

    def test_has_permission_brewhouse_has_no_company(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        self.assertFalse(self.handler.has_permission(brewhouse))

    def test_get_brewhouse_successfully(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        brewhouse_found = self.handler.get_brewhouse()
        self.assertEquals(self.handler._status_code, status.HTTP_200_OK)
        self.assertTrue(brewhouse_found)
        self.assertEquals(self.handler.brewhouse, brewhouse)

    def test_get_brewhouse_does_not_exist(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk + 1)
        brewhouse_found = self.handler.get_brewhouse()
        self.assertFalse(brewhouse_found)
        self.assertIsNone(self.handler.brewhouse)
        self.assertEquals(self.handler._status_code, status.HTTP_404_NOT_FOUND)

    def test_register_waiter_brewhouse_exists_already_in_waiters(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        future = Future()
        self.handler.waiters[brewhouse] = set()
        self.handler.brewhouse = brewhouse
        self.handler.future = future
        self.handler.register_waiter()
        self.assertEquals(self.handler.waiters[brewhouse], {future})

    def test_register_waiter_brewhouse_doesnt_yet_exist_in_waiters(self):
        brewhouse = Brewhouse.objects.create(name="Foo")
        future = Future()
        self.handler.brewhouse = brewhouse
        self.handler.future = future
        self.handler.register_waiter()
        self.assertEquals(self.handler.waiters[brewhouse], {future})

    def test_get_and_check_permission(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)
        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        self.assertTrue(self.handler.get_and_check_permission())

    def test_get_and_check_permission_no_brewhouse(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)
        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk + 1)
        self.assertFalse(self.handler.get_and_check_permission())
        self.assertEquals(self.handler._status_code, status.HTTP_404_NOT_FOUND)

    def test_get_and_check_permission_not_logged_in(self):
        brewhouse = Brewhouse.objects.create(name="Bar")
        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        self.assertFalse(self.handler.get_and_check_permission())
        self.assertEquals(self.handler._status_code, status.HTTP_403_FORBIDDEN)


class TestRecipeInstanceStartHandler(JouliaTestCase):
    """Tests for the RecipeInstanceStartHandler."""

    def setUp(self):
        super(TestRecipeInstanceStartHandler, self).setUp()
        self.handler = recipe_instance.RecipeInstanceStartHandler(self.app,
                                                                  self.request)
        self.handler.request.connection.stream.closed = MagicMock(
            return_value=False)

    def test_active_returns_instance(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)

        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        recipe = Recipe.objects.create(name="Baz")
        instance = RecipeInstance.objects.create(recipe=recipe, active=True,
                                                 brewhouse=brewhouse)

        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        IOLoop.current().run_sync(self.handler.post)
        self.assertEquals(self.handler._status_code, status.HTTP_200_OK)
        self.assertIn(utf8('{{"recipe_instance": {}}}'.format(instance.pk)),
                      self.handler._write_buffer)

    def test_inactive_waits_and_returns_new_instance(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)

        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        recipe = Recipe.objects.create(name="Baz")

        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        instance = RecipeInstance.objects.create(recipe=recipe, active=False,
                                                 brewhouse=brewhouse)

        # TODO(willjschmitt): This test might be flaky because there may be a
        # race condition below. I don't have enough grasp of tornado to be sure
        # though. Beware.
        @gen.coroutine
        def run_and_add_instance():
            self.handler.post()
            instance.active = True
            instance.save()

        IOLoop.current().run_sync(run_and_add_instance, timeout=2.0)
        self.assertEquals(self.handler._status_code, status.HTTP_200_OK)
        self.assertIn(utf8('{{"recipe_instance": {}}}'.format(instance.pk)),
                      self.handler._write_buffer)


class TestRecipeInstanceEndHandler(JouliaTestCase):
    """Tests for the RecipeInstanceEndHandler."""

    def setUp(self):
        super(TestRecipeInstanceEndHandler, self).setUp()
        self.handler = recipe_instance.RecipeInstanceEndHandler(self.app,
                                                                self.request)
        self.handler.request.connection.stream.closed = MagicMock(
            return_value=False)

    def test_inactive_returns_none(self):
        group = Group.objects.create(name="Baz")
        user = User.objects.create(username="john_doe")
        group.user_set.add(user)
        self.force_tornado_login(user)
        brewing_company = BrewingCompany.objects.create(group=group)
        brewery = Brewery.objects.create(name="Foo", company=brewing_company)

        brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
        recipe = Recipe.objects.create(name="Baz")
        RecipeInstance.objects.create(recipe=recipe, active=False,
                                      brewhouse=brewhouse)

        self.handler.request.body_arguments["brewhouse"] = str(brewhouse.pk)
        IOLoop.current().run_sync(self.handler.post, timeout=2.0)
        self.assertEquals(self.handler._status_code, status.HTTP_200_OK)
        self.assertIn(b'{"recipe_instance": null}', self.handler._write_buffer)

    # TODO(willjschmitt): Reenable when we figure out how to solve a future
    # outside of it's code (like through @receiver's from Django.
    # @test_with_fake_session_backend
    # def test_inactive_waits_and_returns_new_instance(self):
    #     group = Group.objects.create(name="Baz")
    #     user = User.objects.create(username="john_doe")
    #     group.user_set.add(user)
    #     self.force_tornado_login(user)
    #     brewing_company = BrewingCompany.objects.create(group=group)
    #     brewery = Brewery.objects.create(name="Foo", company=brewing_company)
    #
    #     brewhouse = Brewhouse.objects.create(name="Bar", brewery=brewery)
    #     recipe = Recipe.objects.create(name="Baz")
    #
    #     self.handler.request.arguments["brewhouse"] = str(brewhouse.pk)
    #     instance = RecipeInstance.objects.create(recipe=recipe, active=True,
    #                                              brewhouse=brewhouse)
    #
    #     # TODO(willjschmitt): This test might be flaky because there may be a
    #     # race condition below. I don't have enough grasp of tornado to be sure
    #     # though. Beware.
    #     @gen.coroutine
    #     def run_and_end_instance():
    #         self.handler.post()
    #         instance.active = False
    #         instance.save()
    #
    #     IOLoop.current().run_sync(run_and_end_instance, timeout=2.0)
    #
    #     self.assertIn(utf8('{{"recipe_instance": {}}}'.format(instance.pk)),
    #                   self.handler._write_buffer)
