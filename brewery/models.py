"""Models for Brewery App. Represents brewing locations, systems, and equipment.
"""

import base64
from datetime import datetime
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
import kubernetes
import logging
import math
from rest_framework.authtoken.models import Token
from uuid import uuid4

from joulia import settings
from joulia import unit_conversions


LOGGER = logging.getLogger(__name__)

# Kubernetes namespace for making deployments to.
KUBERNETES_NAMESPACE = 'default'


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


class BrewingState(models.Model):
    """A state the joulia-controller can be in for a given software release.

    Defines the enum value for what a state is, the number position it is in the
    brewing process, and its description.

    Attributes:
        software_release: the joulia-controller release this state is
            associated with.
        index: the 0-based index for ordering states within a software_release.
            Index must be unique for a software_release.
    """
    software_release = models.ForeignKey(JouliaControllerRelease)
    index = models.IntegerField()
    name = models.TextField()
    description = models.TextField(default="")

    class Meta:
        unique_together = ('software_release', 'index',)


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
    alpha = models.FloatField(default=0.00385)
    zero_resistance = models.FloatField(default=100.0)


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
    vcc = models.FloatField(default=3.3)
    rtd_top_resistance = models.FloatField(default=1000.0)
    amplifier_resistance_a = models.FloatField(default=15000.0)
    amplifier_resistance_b = models.FloatField(default=270000.0)
    offset_resistance_bottom = models.FloatField(default=10000.0)
    offset_resistance_top = models.FloatField(default=100000.0)


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
    rtd = models.ForeignKey(ResistanceTemperatureDevice, null=True)
    amplifier = models.ForeignKey(ResistanceTemperatureDeviceAmplifier,
                                  null=True)
    analog_pin = models.IntegerField(default=0)
    tau_filter = models.FloatField(default=10.0)
    analog_reference = models.FloatField(default=3.3)

    def save(self, *args, **kwargs):
        if self.rtd is None:
            self.rtd = ResistanceTemperatureDevice.objects.create()
        if self.amplifier is None:
            self.amplifier\
                = ResistanceTemperatureDeviceAmplifier.objects.create()

        super(ResistanceTemperatureDeviceMeasurement, self).save(*args,
                                                                 **kwargs)


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
        ResistanceTemperatureDeviceMeasurement, null=True)
    volume = models.FloatField(default=5.0)
    heat_exchanger_conductivity = models.FloatField(default=1.0)

    def save(self, *args, **kwargs):
        if self.temperature_sensor is None:
            self.temperature_sensor\
                = ResistanceTemperatureDeviceMeasurement.objects.create()

        super(MashTun, self).save(*args, **kwargs)


class HeatingElement(models.Model):
    """A resistive heating element, whose power output can be varied by
    adjusting the average applied voltage to it, through PWM.

    Attributes:
        rating: The power output rating of the heating element at full voltage.
            Units: Watts.
        pin: The GPIO pin number for the raspberry pi joulia-controller, which
            turns the heating element on or off.
    """
    rating = models.FloatField(default=5500.0)
    pin = models.IntegerField(default=0)


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
        ResistanceTemperatureDeviceMeasurement, null=True)
    volume = models.FloatField(default=5.0)
    heating_element = models.ForeignKey(HeatingElement, null=True)

    def save(self, *args, **kwargs):
        if self.temperature_sensor is None:
            self.temperature_sensor\
                = ResistanceTemperatureDeviceMeasurement.objects.create()

        if self.heating_element is None:
            self.heating_element = HeatingElement.objects.create()

        super(HotLiquorTun, self).save(*args, **kwargs)


class Pump(models.Model):
    """Liquid pump, which can provide pressure increase to a liquid system for
    moving wort or other liquid between vessels, or for recirculation.

    Attributes:
        pin: The GPIO pin number for the raspberry pi joulia-controller, which
            turns the pump on or off.
    """
    pin = models.IntegerField(default=0)


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
        boil_kettle: Heated vessel with temperature measurement, which doubles
            as a hot liquor tun.
        mash_tun: Vessel for mashing grain into wort.
        main_pump: The main pump for moving liquid between vessels and
            recirculating wort during mash.
        simulated: Boolean indicating if this is a simulated brewhouse.
        simulated_deployment_name: The name of the joulia-controller deployment
            in kubernetes.
        simulated_secret_name: The name of the joulia-controller auth token
            secret in kubernetes.
    """

    BREWHOUSE_SIMULATION_DEPLOYMENT_BASE = 'joulia-controller-simulated'
    BREWHOUSE_SIMULATION_SECRET_BASE = 'joulia-controller-simulated'
    BREWHOUSE_SIMULATION_SECRET_KEY = 'joulia_webserver_authtoken'
    BREWHOUSE_SIMULATION_IMAGE_NAME = (
        'willjschmitt/joulia-controller:latest-simulated')

    name = models.CharField(max_length=64)
    brewery = models.ForeignKey(Brewery, null=True)

    token = models.OneToOneField(Token, null=True)
    user = models.OneToOneField(User, null=True)

    software_version = models.ForeignKey(JouliaControllerRelease, null=True)

    # Equipment configurations.
    boil_kettle = models.ForeignKey(HotLiquorTun, null=True)
    mash_tun = models.ForeignKey(MashTun, null=True)
    main_pump = models.ForeignKey(Pump, null=True)

    # Simulated details.
    simulated = models.BooleanField(default=False)
    simulated_deployment_name = models.CharField(max_length=512, null=True)
    simulated_secret_name = models.CharField(max_length=512, null=True)

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
        if self.boil_kettle is None:
            self.boil_kettle = HotLiquorTun.objects.create()
        if self.mash_tun is None:
            self.mash_tun = MashTun.objects.create()
        if self.main_pump is None:
            self.main_pump = Pump.objects.create()

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

        if self.simulated:
            self._create_simulated_controller()
        else:
            self._delete_simulated_controller()

        super(Brewhouse, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        super(Brewhouse, self).delete(using, keep_parents)

        self._delete_simulated_controller()

    def _create_simulated_controller(self):
        """Creates a kubernetes deployment for a simulated controller."""
        # If the deployment name is already set, we have already created a
        # deployment and do not need to do it again.
        if self.simulated_deployment_name is not None:
            return
        LOGGER.info('Creating simulated brewery for %s.', self)
        uuid = uuid4()
        self._create_kubernetes_secret(uuid)
        self._create_kubernetes_deployment(uuid)

    def _create_kubernetes_secret(self, uuid):
        """Creates a new kubernetes secret.

        Uses the secret base and provided uuid.

        Args:
            uuid: The UUID to append to the secret base for its name.
        """
        self.simulated_secret_name = '{}-{}'.format(
            self.BREWHOUSE_SIMULATION_SECRET_BASE, uuid)

        secret = kubernetes.client.V1Secret(
            metadata=kubernetes.client.V1ObjectMeta(
                name=self.simulated_secret_name
            ),
            string_data={
                self.BREWHOUSE_SIMULATION_SECRET_KEY: self.token.key,
            }
        )
        secret_client = kubernetes.client.CoreV1Api()
        if settings.PRODUCTION_HOST:
            secret_resp = secret_client.create_namespaced_secret(
                namespace=KUBERNETES_NAMESPACE, body=secret)
            LOGGER.info('Created secret response: %s', secret_resp)

    def _create_kubernetes_deployment(self, uuid):
        """Creates a new kubernetes deployment.

        Uses the deployment base and provided uuid.

        Args:
            uuid: The UUID to append to the deployment base for its name.
        """
        self.simulated_deployment_name = str(uuid)

        secret_env_var = kubernetes.client.V1EnvVar(
            name='JOULIA_WEBSERVER_AUTHTOKEN',
            value_from=kubernetes.client.V1EnvVarSource(
                secret_key_ref=kubernetes.client.V1SecretKeySelector(
                    name=self.simulated_secret_name,
                    key=self.BREWHOUSE_SIMULATION_SECRET_KEY
                )
            )
        )
        deployment = kubernetes.client.ExtensionsV1beta1Deployment(
            api_version='extensions/v1beta1',
            kind='Deployment',
            metadata=kubernetes.client.V1ObjectMeta(
                name=self.simulated_deployment_name,
                labels={
                    'app': self.BREWHOUSE_SIMULATION_DEPLOYMENT_BASE,
                }
            ),
            spec=kubernetes.client.ExtensionsV1beta1DeploymentSpec(
                replicas=1,
                selector=kubernetes.client.V1LabelSelector(
                    match_labels={
                        'app': self.BREWHOUSE_SIMULATION_DEPLOYMENT_BASE,
                    }
                ),
                template=kubernetes.client.V1PodTemplateSpec(
                    metadata=kubernetes.client.V1ObjectMeta(
                        labels={
                            'app': self.BREWHOUSE_SIMULATION_DEPLOYMENT_BASE
                        },
                    ),
                    spec=kubernetes.client.V1PodSpec(
                        containers=[
                            kubernetes.client.V1Container(
                                name=self.simulated_deployment_name,
                                image=self.BREWHOUSE_SIMULATION_IMAGE_NAME,
                                image_pull_policy='Always',
                                ports=[
                                    kubernetes.client.V1ContainerPort(
                                        container_port=8888
                                    ),
                                ],
                                env=[
                                    kubernetes.client.V1EnvVar(
                                        name='JOULIA_WEBSERVER_HOST',
                                        value='joulia.io'
                                    ),
                                    kubernetes.client.V1EnvVar(
                                        name='JOULIA_WEBSERVER_HTTP_PROTOCOL',
                                        value='https'
                                    ),
                                    kubernetes.client.V1EnvVar(
                                        name='JOULIA_WEBSERVER_WS_PROTOCOL',
                                        value='wss'
                                    ),
                                    secret_env_var,
                                ]
                            )
                        ]
                    )
                )
            )
        )

        deployment_client = kubernetes.client.ExtensionsV1beta1Api()
        if settings.PRODUCTION_HOST:
            deployment_resp = deployment_client.create_namespaced_deployment(
                namespace=KUBERNETES_NAMESPACE, body=deployment)
            LOGGER.info('Created deployment response: %s', deployment_resp)

    def _delete_simulated_controller(self):
        empty_options = kubernetes.client.V1DeleteOptions()

        deployment_client = kubernetes.client.AppsV1beta1Api()
        if (self.simulated_deployment_name is not None
            and settings.PRODUCTION_HOST):
            deployment_resp = deployment_client.delete_namespaced_deployment(
                self.simulated_deployment_name, KUBERNETES_NAMESPACE,
                empty_options)
            LOGGER.info('Deleted deployment response: %s.', deployment_resp)
        self.simulated_deployment_name = None

        secret_client = kubernetes.client.CoreV1Api()
        if (self.simulated_secret_name is not None
            and settings.PRODUCTION_HOST):
            secret_resp = secret_client.delete_namespaced_secret(
                self.simulated_secret_name, KUBERNETES_NAMESPACE, empty_options)
            LOGGER.info('Deleted secret response: %s.', secret_resp)
        self.simulated_secret_name = None

    def __str__(self):
        return "[{} - {}](#{})".format(self.name, self.brewery, self.pk)


class BeerStyle(models.Model):
    """A style for beer recipes to conform to.

    Attributes:
        name: Human readable name for the recipe.
        low_ibu: Low end IBU value for bitterness.
        high_ibu: High end IBU value for bitterness.
        low_original_gravity: Low end original gravity relative to water.
        high_original_gravity: High end original gravity relative to water.
        low_final_gravity: Low end final gravity relative to water.
        high_final_gravity: Low end final gravity relative to water.
        low_abv: Low end per-unit alcohol by volume.
        high_abv: High end per-unit alcohol by volume.
        low_srm: Low end SRM color in degrees Plato.
        high_srm: High end per-unit alcohol by volume.
    """
    name = models.CharField(max_length=128, unique=True)

    low_ibu = models.IntegerField(default=0)
    high_ibu = models.IntegerField(default=0)
    low_original_gravity = models.FloatField(default=0.0)
    high_original_gravity = models.FloatField(default=0.0)
    low_final_gravity = models.FloatField(default=0.0)
    high_final_gravity = models.FloatField(default=0.0)
    low_abv = models.FloatField(default=0.0)
    high_abv = models.FloatField(default=0.0)
    low_srm = models.FloatField(default=0.0)
    high_srm = models.FloatField(default=0.0)

    def __str__(self):
        return "{}".format(self.name)


class Ingredient(models.Model):
    """An ingredient, which can be used in a recipe.

    Attributes:
        name: The human-readable name for the ingredient.
    """
    name = models.CharField(max_length=256)

    class Meta:
        abstract = True


class YeastIngredient(Ingredient):
    """An ingredient, which ferments sugars in wort into alcohol.

    Attributes:
        low_attenuation: Per-unit min attentuation of yeast.
        high_attenuation: Per-unit max attentuation of yeast.
        low_temperature: Low end of fermentation temperature in degF.
        high_temperature: High end of fermentation temperature in degF.
        low_abv_tolerance: Low end of per-unit alcohol tolerance.
        high_abv_tolerance: Low end of per-unit alcohol tolerance.
    """

    def __init__(self, *args, **kwargs):
        # average_attenuation can be provided as an initialization arg, and
        # low/high_attenuation will be set to that value.
        if 'average_attenuation' in kwargs:
            attenuation = kwargs.pop('average_attenuation')
            kwargs['low_attenuation'] = attenuation
            kwargs['high_attenuation'] = attenuation

        # average_abv_tolerance can be provided as an initialization arg, and
        # low/high_abv_tolerance will be set to that value.
        if 'average_abv_tolerance' in kwargs:
            average_abv_tolerance = kwargs.pop('average_abv_tolerance')
            kwargs['low_abv_tolerance'] = average_abv_tolerance
            kwargs['high_abv_tolerance'] = average_abv_tolerance

        super(YeastIngredient, self).__init__(*args, **kwargs)

    low_attenuation = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    high_attenuation = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    low_temperature = models.FloatField(default=0.0)
    high_temperature = models.FloatField(default=0.0)
    low_abv_tolerance = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    high_abv_tolerance = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    @property
    def average_attenuation(self):
        return (self.low_attenuation + self.high_attenuation) / 2.0

    @property
    def average_abv_tolerance(self):
        return (self.low_abv_tolerance + self.high_abv_tolerance) / 2.0


class Recipe(models.Model):
    """A recipe designed by the brewing company to be used in recipe instances.

    Attributes:
        name: Human readable name for the recipe.
        style: Style for the recipe to conform to.
        company: Brewing Company that owns the recipe.
        volume: Amount of beer to be brewed. Units: gallons.
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

    volume = models.FloatField(default=0.0)

    yeast = models.ForeignKey(YeastIngredient, null=True)

    # Temperatures and times.
    strike_temperature = models.FloatField(default=162.0)
    mashout_temperature = models.FloatField(default=170.0)
    mashout_time = models.FloatField(default=10.0)
    boil_time = models.FloatField(default=60.0)
    cool_temperature = models.FloatField(default=70.0)

    def __str__(self):
        return "{}({})".format(self.name, self.style)

    @property
    def original_gravity(self):
        """Calculates the original gravity for the recipe based on the malt
        ingredient additions and the volume of the recipe. Units: specific
        gravity.
        """
        if self.volume == 0.0:
            return 0.0

        gravity_gallons = 0.0
        for mash_ingredient_addition in self.maltingredientaddition_set.all():
            if mash_ingredient_addition.ingredient is None:
                continue
            amount_pounds = unit_conversions.grams_to_pounds(
                mash_ingredient_addition.amount)
            gravity_offset = (
                mash_ingredient_addition.ingredient.potential_sg_contribution
                - 1.0)
            gravity_gallons += amount_pounds * gravity_offset
        return gravity_gallons / self.volume + 1.0

    @property
    def final_gravity(self):
        """Calculates the final gravity of the recipe.

        Uses original gravity and yeast average attenuation to calculate.

        Units: specific gravity relative to water.
        """
        if self.yeast is None:
            return self.original_gravity

        og = self.original_gravity
        return og - (og - 1.0) * self.yeast.average_attenuation

    @property
    def abv(self):
        """Calculates the per-unit alcohol by volume of the recipe.

        Units: per-unit.
        """
        return (self.original_gravity - self.final_gravity) * 1.3125

    @property
    def ibu(self):
        """Calculates the bitterness of the recipe based on the bittering
        ingredient additions and the volume of the recipe. Units: IBUs.

        Calculation based from formulae in:
        http://howtobrew.com/book/section-1/hops/hop-bittering-calculations
        """
        if self.volume == 0.0:
            return 0.0

        ibu = 0.0
        for addition in self.bitteringingredientaddition_set.all():
            if addition.ingredient is None:
                continue

            if addition.step_added != BREWING_STEP_CHOICES__BOIL:
                continue
            amount_ounces = unit_conversions.grams_to_ounces(addition.amount)
            aau = amount_ounces * addition.ingredient.alpha_acid_weight * 100.0
            gravity_utilization = 1.65 * 0.000125**(self.original_gravity - 1.0)
            time_utilization \
                = (1.0 - math.exp(-0.04 * addition.time_added)) / 4.15
            utilization = gravity_utilization * time_utilization
            ibu_addition = aau * utilization * 75 / self.volume
            ibu += ibu_addition
        return ibu

    @property
    def srm(self):
        """Calculates the SRM color of the wort based on the mash ingredient
        additions. Units: SRM.
        """
        if self.volume == 0.0:
            return 0.0

        mcu = 0.0
        for addition in self.maltingredientaddition_set.all():
            if addition.ingredient is None:
                continue

            mcu += unit_conversions.grams_to_pounds(addition.amount) \
                * addition.ingredient.color / self.volume
        return 1.4922 * mcu**0.6859


class MaltIngredient(Ingredient):
    """An ingredient, which can be used in a recipe, and provides sugar for
    fermentation.

    Attributes:
        potential_sg_contribution: The potential sugar contribution to a mash.
            Units: Specific gravity (relative to water) with 1 pound added to
            1 gallon of water.
        color: The color contribution from the grain to the mash. Units: SRM.
    """
    potential_sg_contribution = models.FloatField(
        default=1.0, validators=(MinValueValidator(1.0),))
    color = models.FloatField(default=1.0)


class BitteringIngredient(Ingredient):
    """An ingredient, which provides bitterness to a recipe, like hops.

    Attributes:
        alpha_acid_weight: Per-unit amount of alpha acid by weight of the hops.
    """
    alpha_acid_weight = models.FloatField(default=0.0)


BREWING_STEP_CHOICES__MASH = '0'
BREWING_STEP_CHOICES__BOIL = '1'
BREWING_STEP_CHOICES__WHIRLPOOL = '2'
BREWING_STEP_CHOICES__FERMENTATION = '3'
BREWING_STEP_CHOICES__CONDITIONING = '4'
BREWING_STEP_CHOICES = (
    (BREWING_STEP_CHOICES__MASH, 'MASH',),
    (BREWING_STEP_CHOICES__BOIL, 'BOIL',),
    (BREWING_STEP_CHOICES__WHIRLPOOL, 'WHIRLPOOL',),
    (BREWING_STEP_CHOICES__FERMENTATION, 'FERMENTATION',),
    (BREWING_STEP_CHOICES__CONDITIONING, 'CONDITIONING',),
)

UNITS_CHOICES__POUNDS = '0'
UNITS_CHOICES__OUNCES = '1'
UNITS_CHOICES__GRAMS = '2'
UNITS_CHOICES__KILOGRAMS = '3'
UNITS_CHOICES = (
    (UNITS_CHOICES__POUNDS, 'pounds',),
    (UNITS_CHOICES__OUNCES, 'ounces',),
    (UNITS_CHOICES__GRAMS, 'grams',),
    (UNITS_CHOICES__KILOGRAMS, 'kilograms',),
)


class MaltIngredientAddition(models.Model):
    """An MaltIngredient entry in a Recipe.

    Attributes:
        recipe: The recipe this ingredient addition is associated with.
        ingredient: The ingredient definition with its properties.
        amount: The amount of the ingredient to add, in grams.
        units: The units to use in the presentation to the user. Only affects
            view layer, and not any underlying business logic.
        step_added: The step this ingredient will be added to.
        time_added: Time relative to the end of this step this ingredient will
            be added. Units: seconds.
    """
    recipe = models.ForeignKey(Recipe)
    ingredient = models.ForeignKey(MaltIngredient, null=True)
    amount = models.FloatField(default=0.0)
    units = models.CharField(max_length=1, choices=UNITS_CHOICES,
                             default=UNITS_CHOICES__POUNDS)
    step_added = models.CharField(max_length=1, choices=BREWING_STEP_CHOICES)
    time_added = models.IntegerField(default=0)


class BitteringIngredientAddition(models.Model):
    """An BitteringIngredient entry in a Recipe.

    Attributes:
        recipe: The recipe this ingredient addition is associated with.
        ingredient: The ingredient definition with its properties.
        amount: The amount of the ingredient to add, in grams.
        units: The units to use in the presentation to the user. Only affects
            view layer, and not any underlying business logic.
        step_added: The step this ingredient will be added to.
        time_added: Time relative to the end of this step this ingredient will
            be added. Units: seconds.
    """
    recipe = models.ForeignKey(Recipe)
    ingredient = models.ForeignKey(BitteringIngredient, null=True)
    amount = models.FloatField(default=0.0)
    units = models.CharField(max_length=1, choices=UNITS_CHOICES,
                             default=UNITS_CHOICES__OUNCES)
    step_added = models.CharField(max_length=1, choices=BREWING_STEP_CHOICES)
    time_added = models.IntegerField(default=0)


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
    VARIABLE_TYPE_CHOICES = (
        ("value", "value"),
        ("override", "override"),
    )

    name = models.CharField(max_length=64)
    brewhouse = models.ForeignKey(Brewhouse, null=True)
    variable_type = models.CharField(max_length=32,
                                     choices=VARIABLE_TYPE_CHOICES,
                                     default="value")

    def __str__(self):
        brewhouse = self.brewhouse.name if self.brewhouse is not None else None
        return "{}-{}".format(brewhouse, self.name)

    class Meta:
        unique_together = ('name', 'brewhouse', 'variable_type',)


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

    class Meta:
        get_latest_by = 'time'

    def __str__(self):
        return "{} - {} @ {}".format(
            self.sensor.name, self.value, self.time)
