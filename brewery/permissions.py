"""Django rest framework permissions for the brewery app rest end points.
"""

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

from brewery import models


class IsAdminToEdit(permissions.BasePermission):
    """Must be a superuser to edit, but get accesses are okay for everyone."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_superuser


class IsMember(permissions.BasePermission):
    """Checks the current user is a member of the requested brewing company."""
    def has_object_permission(self, request, view, brewing_company):
        return is_member_of_brewing_company(request.user, brewing_company)


class IsMemberOfBrewingCompany(permissions.BasePermission):
    """Checks the current user is a member of the brewing company associated
    with the requested brewery.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Makes sure a user can only create new Breweries in a BrewingCompany
        # they are a member of.
        company_pk = request.POST.get("company", None)
        if company_pk is not None:
            company = models.BrewingCompany.objects.get(pk=company_pk)
            return is_member_of_brewing_company(request.user, company)

        return True

    def has_object_permission(self, request, view, brewery):
        return is_member_of_brewing_company(request.user, brewery.company)


class IsMemberOfBrewery(permissions.BasePermission):
    """Checks the current user is a member of the brewing company that owns the
    brewery the brewing equipment is associated with.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Makes sure a user can only create new Brewhouses in a Brewery they are
        # a member of.
        brewery_pk = request.POST.get("brewery", None)
        if brewery_pk is not None:
            brewery = models.Brewery.objects.get(pk=brewery_pk)
            company = brewery.company
            return is_member_of_brewing_company(request.user, company)

        return True

    def has_object_permission(self, request, view, brewing_equipment):
        brewing_company = brewing_equipment.brewery.company
        return is_member_of_brewing_company(request.user, brewing_company)


class OwnsRecipe(permissions.BasePermission):
    """Checks the current user is a member of the brewing company that owns the
    recipe object is associated with.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Makes sure a user can only create new Recipes in a BrewingCompany they
        # are a member of.
        recipe_pk = request.POST.get("recipe", None)
        if recipe_pk is not None:
            recipe = models.Recipe.objects.get(pk=recipe_pk)
            company = recipe.company
            return is_member_of_brewing_company(request.user, company)

        return True

    def has_object_permission(self, request, view, obj):
        brewing_company = obj.recipe.company
        return is_member_of_brewing_company(request.user, brewing_company)


class OwnsSensor(permissions.BasePermission):
    """Checks the current user is a member of the brewing company that owns the
    ``sensor`` object associated with.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Makes sure a user can only create new Recipes in a BrewingCompany they
        # are a member of.
        sensor_pk = request.POST.get("sensor", None)
        if sensor_pk is not None:
            sensor = models.AssetSensor.objects.get(pk=sensor_pk)
            company = sensor.brewhouse.brewery.company
            return is_member_of_brewing_company(request.user, company)

        return True

    def has_object_permission(self, request, view, obj):
        brewing_company = obj.sensor.brewhouse.brewery.company
        return is_member_of_brewing_company(request.user, brewing_company)


def is_member_of_brewing_company(user, brewing_company):
    """Checks the user is a member of the brewing_company group.

    Args:
        user: The django user to check membership for.
        brewing_company: The BrewingCompany to check membership in its
            associated group.
    """
    if brewing_company.group is None:
        return False

    return user in brewing_company.group.user_set.all()
