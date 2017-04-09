"""Test for the tornado_sockets.views.recipe_instance module."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from tornado.concurrent import Future
from unittest.mock import Mock

from brewery.models import Brewery
from brewery.models import Brewhouse
from brewery.models import BrewingCompany
from brewery.models import Recipe
from brewery.models import RecipeInstance
from testing.fake_session_backend import test_with_fake_session_backend
from testing.test import JouliaTestCase
from tornado_sockets.views import recipe_instance


class TestRecipeInstanceHandler(JouliaTestCase):
    """Tests for the RecipeInstanceHandler class."""

    def setUp(self):
        app = Mock()
        app.ui_methods = {}
        request = Mock()
        cookie = Mock(value="abcdefg")
        request.cookies = {settings.SESSION_COOKIE_NAME: cookie}
        self.handler = recipe_instance.RecipeInstanceHandler(app, request)

    def test_post(self):
        with self.assertRaises(NotImplementedError):
            self.handler.post()

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

    @test_with_fake_session_backend
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

    #IOLoop.current().run_sync(lambda: self._connect(address))