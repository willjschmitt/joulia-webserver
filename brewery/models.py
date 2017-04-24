"""Models for Brewery App. Represents brewing locations, systems, and equipment.
"""

from datetime import datetime
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from rest_framework.authtoken.models import Token


class BrewingCompany(models.Model):
    """An organizational group as a Brewing Company.

    Attributes:
        group: A django auth group of users associated with this brewing
            company.
        name: A pass-through property to the group's name.
    """
    group = models.OneToOneField(Group, null=True)

    @property
    def name(self):
        """Simple alias to the associated group name."""
        return self.group.name if self.group else None

    def __str__(self):
        return "{}".format(self.group.name)


class Brewery(models.Model):
    """A physical brewing facility associated with a brewing company
    organization.

    Attributes:
        name: A human-readable name for the brewing location.
        company: BrewingCompany that the location is owned by.
    """
    name = models.CharField(max_length=256)
    company = models.ForeignKey(BrewingCompany, null=True)

    def __str__(self):
        return "{}".format(self.name)


class Brewhouse(models.Model):
    """A brewhouse facility for mashing and boiling a recipe instance.

    Has a physical control system that correlates with this object. This is why
    a token is provided for authentication purposes.

    Attributes:
        name: Human readable name for the brewhouse.
        brewery: Brewery location the Brewhouse is located at.
        token: A django rest framework token associated with a user at the
            BrewingCompany, who provides authentication for the Brewhouse to be
            accessed and transmitted with.
        active: A property checking if there are any active recipe instances on
            the Brewhouse currently.
        active_recipe_instance: A property retrieving the currently active
            RecipeInstance if one exists.
    """
    name = models.CharField(max_length=64)
    brewery = models.ForeignKey(Brewery, null=True)

    token = models.ForeignKey(Token, null=True)

    @property
    def active(self):
        """Checks if there is an active recipe instance associated with this
        Brewhouse.

        Returns: True if there is an active instance. False if there are no
            active instances.
        """
        return self.recipeinstance_set.filter(active=True).count() == 1

    @property
    def active_recipe_instance(self):
        """Retrieves the active recipe instance if the brewhouse is active.

        Returns: RecipeInstance object currently active on this Brewhouse if one
            exists. If one does not exist, returns None.
        """
        try:
            return self.recipeinstance_set.get(active=True)
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return "{} - {}".format(self.name, self.brewery)


class BeerStyle(models.Model):
    """A style for beer recipes to conform to.

    Attributes:
        name: Human readable name for the recipe.
    """
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return "{}".format(self.name)


class Recipe(models.Model):
    """A recipe designed by the brewing company to be used in recipe instances.

    Attributes:
        name: Human readable name for the recipe.
        style: Style for the recipe to conform to.
    """
    name = models.CharField(max_length=64)
    style = models.ForeignKey(BeerStyle, null=True)

    def __str__(self):
        return "{}({})".format(self.name, self.style)


class RecipeInstance(models.Model):
    """An instance a recipe was brewed on a brewhouse.

    Attributes:
        recipe: Recipe the instance is conforming to.
        date: The date this instance was started.
        brewhouse: The brewhouse equipment this was brewed on.
        active: If the recipe instance is still in progress.
        original_gravity: The specific gravity of the unfermented wort.
        final_gravity: The specific gravity of the fermented wort.
    """
    recipe = models.ForeignKey(Recipe)
    date = models.DateField(default=datetime.now)
    brewhouse = models.ForeignKey(Brewhouse, null=True)
    active = models.BooleanField(default=False)

    original_gravity = models.DecimalField(null=True, decimal_places=3,
                                           max_digits=4)
    final_gravity = models.DecimalField(null=True, decimal_places=3,
                                        max_digits=4)

    def save(self, *args, **kwargs):
        # Make sure we don't initialize a recipe instance on an already active
        # brewhouse.
        active = RecipeInstance.objects.filter(
            brewhouse=self.brewhouse, active=True)
        already_active = active.count()
        if self.active and not self.pk and already_active > 0:
            raise RuntimeError("Cannot instantiate recipe instance while one is"
                               " already active on brewhouse.")

        super(RecipeInstance, self).save(*args, **kwargs)

    def __str__(self):
        return "{} - {} ({}) {}".format(
            self.recipe.name, self.date,
            self.brewhouse.name if self.brewhouse else None,
            "ACTIVE" if self.active else "INACTIVE")


class AssetSensor(models.Model):
    """A physical sensor associated with a brewhouse.

    Attributes:
        name: A non-human-readable name expressing the sensor like
            "brewkettle__temperature", indicating the temperature of the brew
            kettle.
        brewery: The brewhouse the sensor is associated with.
    """
    name = models.CharField(max_length=64)
    brewhouse = models.ForeignKey(Brewhouse, null=True)

    def __str__(self):
        brewhouse = self.brewhouse.name if self.brewhouse is not None else None
        return "{}-{}".format(brewhouse, self.name)


class TimeSeriesDataPoint(models.Model):
    """A single data point measured by an AssetSensor.

    Attributes:
        sensor: the sensor the datapoint was measured by.
        recipe_instance: An instance of equipment use that the data should be
            associated with.
        time: The time of the measurement.
        value: A (float) value measured by the sensor. Intention is to extend
            this to more variable types in a better way.
    """
    # TODO(willjschmitt): Move time series data into a nosql database.
    sensor = models.ForeignKey(AssetSensor)
    recipe_instance = models.ForeignKey(RecipeInstance)

    time = models.DateTimeField(default=timezone.now)
    value = models.FloatField(null=True)

    def __str__(self):
        return "{} - {} @ {}".format(
            self.sensor.name, self.value, self.time)
