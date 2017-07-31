"""Models for Brewery App. Represents brewing locations, systems, and equipment.
"""

from datetime import datetime
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from rest_framework.authtoken.models import Token
from uuid import uuid4


class JouliaControllerRelease(models.Model):
    """A software release for the Joulia Controller software.

    Attributes:
        commit_hash: A full 40 character length SHA-1 hash for the commit this
            release should point to.
        release_time: The time the release was generated and accepted for
            distribution.
    """
    commit_hash = models.CharField(max_length=40)
    release_time = models.DateTimeField(default=timezone.now)


class InvalidUserError(Exception):
    """An error for an invalid association of a user with a BrewingCompany."""
    pass


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


class ResistanceTemperatureDevice(models.Model):
    """An RTD sensor device itself. Just the electrical properties of the
    device.

    Attributes:
        alpha: The RTD resistance coefficient. Units: Ohms/degC.
        zero_resistance: The resistance of the RTD at 0degC. Units: Ohms.
    """
    alpha = models.FloatField()
    zero_resistance = models.FloatField()


class ResistanceTemperatureDeviceAmplifier(models.Model):
    """An amplifier circuit, which amplifies the resistance measurement from an
    RTD into a usable voltage range.

    Assumes an RTD input as the bottom of a resistive voltage divider circuit,
    which is then differenced against a voltage, which provides an offset/lower
    bound to the resistance measurement. The differencer has an amplifying gain.

    Attributes:
        vcc: The input voltage to the RTD voltage divider. Units: Volts.
        rtd_top_resistance: The resistance of the top resistor in the voltage
            divider circuit, where the RTD is the bottom resistance. This
            converts the RTD resistance into a voltage. Units: Ohms.
        amplifier_resistance_a: Resistor, which forms the denominator in the
            differential amplifier gain as ``amplifier_resistance_b /
            amplifier_resistance_b``. Units: Ohms.
        amplifier_resistance_b: Resistor, which forms the numerator in the
            differential amplifier gain as ``amplifier_resistance_b /
            amplifier_resistance_b``. Units: Ohms.
        offset_resistance_bottom: Resistor, which forms the bottom of the offset
            voltage follower, which with the offset_resistance_top, forms a
            reference voltage to difference the RTD against. Effectively forms
            a lower bounds for the RTD measurement. Units: Ohms.
        offset_resistance_top: Resistor, which forms the top of the offset
            voltage follower, which with the offset_resistance_bottom, forms a
            reference voltage to difference the RTD against. Effectively forms
            a lower bounds for the RTD measurement. Units: Ohms.
    """
    vcc = models.FloatField()
    rtd_top_resistance = models.FloatField()
    amplifier_resistance_a = models.FloatField()
    amplifier_resistance_b = models.FloatField()
    offset_resistance_bottom = models.FloatField()
    offset_resistance_top = models.FloatField()


class ResistanceTemperatureDeviceMeasurement(models.Model):
    """An RTD sensor device with an amplifier circuit and multi-channel A/D
    measurement device.

    Attributes:
        rtd: The RTD device itself, which adjusts its resistance based on the
            temperature.
        amplifier: An amplifier circuit for amplifying the resistance of the
            ``rtd`` into a usable voltage range up to ``analog_reference``.
        analog_pin: The pin number for the channel on the A/D device, where the
            voltage should be measured.
        tau_filter: The time constant, which should be applied to the measured
            raw signal to filter out noise. Is used in the transfer function
            1/(1+s*tau). Units: Seconds.
        analog_reference: The voltage reference used by the A/D chip for
            converting the analog signal into the resolution of digital data it
            can provide. Units: Volts.
    """
    rtd = models.ForeignKey(ResistanceTemperatureDevice)
    amplifier = models.ForeignKey(ResistanceTemperatureDeviceAmplifier)
    analog_pin = models.IntegerField()
    tau_filter = models.FloatField(default=10.0)
    analog_reference = models.FloatField(default=3.3)


class MashTun(models.Model):
    """A vessel for mashing grain in.

    Attributes:
        temperature_sensor: An RTD measurement system measuring the temperature
            of the output liquid from the mash tun in a recirculating
            configuration.
        volume: Size of the mash tun vessel. Units: gallons.
        heat_exchanger_conductivity: The rough conductivity for heat energy from
            the hot liquor tun into the heat exchanger into the mash tun. This
            does not yet take into account flow rates, and should roughly be
            calibrated on the sytem typical flow rate. It's mostly a heuristic
            value for tuning the mash tun PI temperature regulator. Units:
            Watts/(delta degF).
    """
    temperature_sensor = models.ForeignKey(
        ResistanceTemperatureDeviceMeasurement)
    volume = models.FloatField()
    heat_exchanger_conductivity = models.FloatField()


class HeatingElement(models.Model):
    """A resistive heating element, whose power output can be varied by
    adjusting the average applied voltage to it, through PWM.

    Attributes:
        rating: The power output rating of the heating element at full voltage.
            Units: Watts.
        pin: The GPIO pin number for the raspberry pi joulia-controller, which
            turns the heating element on or off.
    """
    rating = models.FloatField()
    pin = models.IntegerField()


class HotLiquorTun(models.Model):
    """A hot liquor tun, which may double for a boil kettle. Has temperature
    measurement and heating capabilities, as well as liquid extraction and heat
    exchanger capabilities.

    Attributes:
        temperature_sensor: An RTD measurement system measuring the temperature
            of the vessel as long as it has liquid in it.
        volume: Size of the HLT. Units: gallons.
        heating_element: Heating element, capable of adding thermal energy into
            the liquid in the HLT.
    """
    temperature_sensor = models.ForeignKey(
        ResistanceTemperatureDeviceMeasurement)
    volume = models.FloatField()
    heating_element = models.ForeignKey(HeatingElement)


class Pump(models.Model):
    """Liquid pump, which can provide pressure increase to a liquid system for
    moving wort or other liquid between vessels, or for recirculation.

    Attributes:
        pin: The GPIO pin number for the raspberry pi joulia-controller, which
            turns the pump on or off.
    """
    pin = models.IntegerField()


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
        user: A django user, which will be autoset by the save method if not
            set. Will be a user that is a member of the BrewingCompany this
            Brewhouse is associated with. The token and user will be tied
            together. They are both saved here to express the direct coupling
            the autogenerated user and token have with the Brewhouse.
        software_version: The JouliaControllerRelease instance the
            Joulia-Controller software on this brewhouse is currently running.
            Controllers will use this to determine if there is a newer version
            for them to upgrade to.
        active: A property checking if there are any active recipe instances on
            the Brewhouse currently.
        active_recipe_instance: A property retrieving the currently active
            RecipeInstance if one exists.
    """
    name = models.CharField(max_length=64)
    brewery = models.ForeignKey(Brewery, null=True)

    token = models.OneToOneField(Token, null=True)
    user = models.OneToOneField(User, null=True)

    software_version = models.ForeignKey(JouliaControllerRelease, null=True)

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

    def save(self, *args, **kwargs):
        """Automatically sets the user and token attributes, making sure the
        User has permission to edit this Brewhouse and related items.
        """
        # If there is not a brewing company associated with the Brewhouse, just
        # go ahead and save it immediately, since it cannot be auth'ed with
        # permissions anyways.
        if self.brewery is None or self.brewery.company is None:
            return super(Brewhouse, self).save(*args, **kwargs)

        if self.user is None:
            # These name choices are largely arbitrary, but they will
            #   1. Ensure uniqueness of username.
            #   2. Provide a human-readable name with a name
            #      <brewing_company.name>:<brewery.name>, <name>.
            username = uuid4()
            first_name = self.name
            last_name = "{}:{}".format(self.brewery.company.name,
                                       self.brewery.name)
            self.user = User.objects.create(
                username=username, first_name=first_name, last_name=last_name)
            self.user.groups.add(self.brewery.company.group)
            self.user.set_unusable_password()
            self.user.save()

        group_count = self.user.groups.count()
        if group_count != 1:
            raise InvalidUserError(
                "User associated with Brewhouse {} does not have exactly one"
                " group associated with it; has: {}.".format(self, group_count))

        if self.user not in self.brewery.company.group.user_set.all():
            raise InvalidUserError(
                "User associated with Brewhouse {} is not a member of the"
                " BrewingCompany associated with it.".format(self))

        if self.token is None:
            self.token = Token.objects.create(user=self.user)

        if self.token.user != self.user:
            raise InvalidUserError("Token associated with Brewhouse {} is not"
                                   " associated with user.")

        super(Brewhouse, self).save(*args, **kwargs)

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
        company: Brewing Company that owns the recipe.
        strike_temperature: Temperature to raise Hot Liquor Tun to before strike
            and pumping the Hot Liquor into the Mash Tun. Units: degrees
            Fahrenheit.
        mashout_temperature: Temperature to raise the mash temperature to after
            mash is done to stop enzymatic process and decrease visosity of
            wort. Units: degrees Fahrenheit.
        mashout_time: Time to hold the mash at the ``mashout_temperature``.
            Units: minutes.
        boil_time: Time to boil the wort. Units: minutes.
        cool_temperature: Temperature to bring wort down to after boiling.
            Units: degrees Fahrenheit.
    """
    name = models.CharField(max_length=64, default="Unnamed")
    style = models.ForeignKey(BeerStyle, null=True)

    company = models.ForeignKey(BrewingCompany, null=True)

    # Temperatures and times.
    strike_temperature = models.FloatField(default=162.0)
    mashout_temperature = models.FloatField(default=170.0)
    mashout_time = models.FloatField(default=10.0)
    boil_time = models.FloatField(default=60.0)
    cool_temperature = models.FloatField(default=70.0)

    def __str__(self):
        return "{}({})".format(self.name, self.style)


class MashPoint(models.Model):
    """A temperature set point as a time, temperature pair.

    Attributes:
        recipe: The recipe this mash point applies to.
        index: The index number for the mash point. Used for ordering mash
            points.
        time: Amount of time to mash at this temperature for (minutes).
        temperature: Temperature to mash at (degrees Fahrenheit).
    """
    recipe = models.ForeignKey(Recipe)
    index = models.IntegerField()
    time = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        if self.index is None:
            new_index = 0
            for mash_point in self.recipe.mashpoint_set.all():
                if mash_point.index >= new_index:
                    new_index = mash_point.index + 1
            self.index = new_index
        else:
            for mash_point in self.recipe.mashpoint_set.all():
                if self.index == mash_point.index and self != mash_point:
                    raise RuntimeError("A MashPoint cannot be saved with the "
                                       "same index as another in a Recipe.")
        super(MashPoint, self).save(*args, **kwargs)


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
        source: A short string that can be used to identify the source of a data
            point. Intentionally short, so each data point doesn't grow too much
            in size, since this table will have a large number of points. Should
            really only be used to identify a data point in subscribers to make
            sure we don't send the data point to a waiter, who was the one that
            sent it.
    """
    # TODO(willjschmitt): Move time series data into a nosql database.
    sensor = models.ForeignKey(AssetSensor)
    recipe_instance = models.ForeignKey(RecipeInstance)

    time = models.DateTimeField(default=timezone.now)
    value = models.FloatField(null=True)

    source = models.TextField(max_length=4, null=True)

    def __str__(self):
        return "{} - {} @ {}".format(
            self.sensor.name, self.value, self.time)
