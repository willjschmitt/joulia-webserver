"""Unit tests for the brewery.serializers module."""

import copy
import datetime
from django.test import TestCase

from brewery import models
from brewery import serializers

VALID_RTD_DATA = {
    'alpha': 0.12345,
    'zero_resistance': 123.45,
}

VALID_AMP_DATA = {
    'vcc': 1.25,
    'rtd_top_resistance': 1000.0,
    'amplifier_resistance_a': 15000.0,
    'amplifier_resistance_b': 270000.0,
    'offset_resistance_bottom': 10000.0,
    'offset_resistance_top': 1000000.0,
}

VALID_TEMPERATURE_SENSOR_DATA = {
    'rtd': copy.deepcopy(VALID_RTD_DATA),
    'amplifier': copy.deepcopy(VALID_AMP_DATA),
}

VALID_MASH_TUN_DATA = {
    'temperature_sensor': copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA),
    'volume': 5.0,
    'heat_exchanger_conductivity': 1.0,
}

VALID_HEATING_ELEMENT_DATA = {
    'rating': 5500.0,
    'pin': 0,
}

VALID_HOT_LIQUOR_TUN_DATA = {
    'temperature_sensor': copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA),
    'volume': 5.0,
    'heating_element': copy.deepcopy(VALID_HEATING_ELEMENT_DATA),
}

VALID_PUMP_DATA = {
    'pin': 0,
}

VALID_BREWHOUSE_DATA = {
    'boil_kettle': copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA),
    'mash_tun': copy.deepcopy(VALID_MASH_TUN_DATA),
    'main_pump': copy.deepcopy(VALID_PUMP_DATA),
}


class ResistanceTemperatureDeviceMeasurementSerializerTest(TestCase):
    @staticmethod
    def get_serializer():
        return serializers.ResistanceTemperatureDeviceMeasurementSerializer()

    def test_create_creates_rtd(self):
        serializer = self.get_serializer()
        temperature_sensor = serializer.create(
            copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA))
        self.assertEquals(temperature_sensor.rtd.alpha, VALID_RTD_DATA['alpha'])

    def test_create_creates_amplifier(self):
        serializer = self.get_serializer()
        temperature_sensor = serializer.create(
            copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA))
        self.assertEquals(temperature_sensor.amplifier.vcc,
                          VALID_AMP_DATA['vcc'])

    def test_update_updates_rtd(self):
        serializer = self.get_serializer()
        temperature_sensor = serializer.create(
            copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA))
        new_alpha = 0.54321
        self.assertNotEquals(new_alpha, VALID_RTD_DATA['alpha'])
        new_rtd_data = copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA)
        new_rtd_data['rtd']['alpha'] = new_alpha
        temperature_sensor = serializer.update(temperature_sensor,
                                               copy.deepcopy(new_rtd_data))
        self.assertEquals(temperature_sensor.rtd.alpha, new_alpha)

    def test_update_updates_amplifier(self):
        serializer = self.get_serializer()
        temperature_sensor = serializer.create(
            copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA))
        new_vcc = 2.15
        self.assertNotEquals(new_vcc, VALID_AMP_DATA['vcc'])
        new_rtd_data = copy.deepcopy(VALID_TEMPERATURE_SENSOR_DATA)
        new_rtd_data['amplifier']['vcc'] = new_vcc
        temperature_sensor = serializer.update(temperature_sensor,
                                               copy.deepcopy(new_rtd_data))
        self.assertEquals(temperature_sensor.amplifier.vcc, new_vcc)


class MashTunSerializerTest(TestCase):
    @staticmethod
    def get_serializer():
        return serializers.MashTunSerializer()

    def test_create(self):
        serializer = self.get_serializer()
        mash_tun = serializer.create(copy.deepcopy(VALID_MASH_TUN_DATA))
        self.assertEquals(mash_tun.temperature_sensor.rtd.alpha,
                          VALID_RTD_DATA['alpha'])

    def test_update(self):
        serializer = self.get_serializer()
        mash_tun = serializer.create(copy.deepcopy(VALID_MASH_TUN_DATA))
        new_alpha = 0.54321
        self.assertNotEquals(new_alpha, VALID_RTD_DATA['alpha'])
        new_mash_tun_data = copy.deepcopy(VALID_MASH_TUN_DATA)
        new_mash_tun_data['temperature_sensor']['rtd']['alpha'] = new_alpha
        mash_tun = serializer.update(mash_tun, copy.deepcopy(new_mash_tun_data))
        self.assertEquals(mash_tun.temperature_sensor.rtd.alpha, new_alpha)


class HotLiquorTunSerializerTest(TestCase):
    @staticmethod
    def get_serializer():
        return serializers.HotLiquorTunSerializer()

    def test_create_creates_heating_element(self):
        serializer = self.get_serializer()
        hot_liquor_tun = serializer.create(
            copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA))
        self.assertEquals(hot_liquor_tun.heating_element.rating,
                          VALID_HEATING_ELEMENT_DATA['rating'])

    def test_update_updates_heating_element(self):
        serializer = self.get_serializer()
        hot_liquor_tun = serializer.create(
            copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA))
        new_rating = 6600.0
        self.assertNotEquals(new_rating, VALID_HEATING_ELEMENT_DATA['rating'])
        new_hlt_data = copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA)
        new_hlt_data['heating_element']['rating'] = new_rating
        hot_liquor_tun = serializer.update(hot_liquor_tun,
                                           copy.deepcopy(new_hlt_data))
        self.assertEquals(hot_liquor_tun.heating_element.rating, new_rating)

    def test_create_creates_temperature_sensor(self):
        serializer = self.get_serializer()
        hot_liquor_tun = serializer.create(
            copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA))
        self.assertEquals(hot_liquor_tun.temperature_sensor.rtd.alpha,
                          VALID_RTD_DATA['alpha'])

    def test_update_updates_temperature_sensor(self):
        serializer = self.get_serializer()
        hot_liquor_tun = serializer.create(
            copy.deepcopy(VALID_HOT_LIQUOR_TUN_DATA))
        new_alpha = 0.54321
        self.assertNotEquals(new_alpha, VALID_RTD_DATA['alpha'])
        new_hlt_data = copy.deepcopy(VALID_MASH_TUN_DATA)
        new_hlt_data['temperature_sensor']['rtd']['alpha'] = new_alpha
        hot_liquor_tun = serializer.update(hot_liquor_tun,
                                           copy.deepcopy(new_hlt_data))
        self.assertEquals(hot_liquor_tun.temperature_sensor.rtd.alpha,
                          new_alpha)


class BrewhouseSerializerTest(TestCase):
    """Tests for the BrewhouseSerializer."""

    @staticmethod
    def get_serializer():
        return serializers.BrewhouseSerializer()

    def test_create_creates_boil_kettle(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        self.assertEquals(brewhouse.boil_kettle.volume,
                          VALID_HOT_LIQUOR_TUN_DATA['volume'])

    def test_update_updates_boil_kettle(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        new_volume = 6.0
        self.assertNotEquals(new_volume, VALID_HOT_LIQUOR_TUN_DATA['volume'])
        new_brewhouse_data = copy.deepcopy(VALID_BREWHOUSE_DATA)
        new_brewhouse_data['boil_kettle']['volume'] = new_volume
        brewhouse = serializer.update(brewhouse,
                                      copy.deepcopy(new_brewhouse_data))
        self.assertEquals(brewhouse.boil_kettle.volume, new_volume)

    def test_create_creates_mash_tun(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        self.assertEquals(brewhouse.mash_tun.volume,
                          VALID_MASH_TUN_DATA['volume'])

    def test_update_updates_mash_tun(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        new_volume = 6.0
        self.assertNotEquals(new_volume, VALID_MASH_TUN_DATA['volume'])
        new_brewhouse_data = copy.deepcopy(VALID_BREWHOUSE_DATA)
        new_brewhouse_data['mash_tun']['volume'] = new_volume
        brewhouse = serializer.update(brewhouse,
                                      copy.deepcopy(new_brewhouse_data))
        self.assertEquals(brewhouse.mash_tun.volume, new_volume)

    def test_create_creates_main_pump(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        self.assertEquals(brewhouse.main_pump.pin, VALID_PUMP_DATA['pin'])

    def test_update_updates_main_pump(self):
        serializer = self.get_serializer()
        brewhouse = serializer.create(copy.deepcopy(VALID_BREWHOUSE_DATA))
        new_pin = 2
        self.assertNotEquals(new_pin, VALID_PUMP_DATA['pin'])
        new_brewhouse_data = copy.deepcopy(VALID_BREWHOUSE_DATA)
        new_brewhouse_data['main_pump']['pin'] = new_pin
        brewhouse = serializer.update(brewhouse,
                                      copy.deepcopy(new_brewhouse_data))
        self.assertEquals(brewhouse.main_pump.pin, new_pin)


class RecipeSerializerTest(TestCase):
    """Tests for the RecipeSerializer."""

    def test_get_last_brewed_no_instance(self):
        recipe = models.Recipe.objects.create(name="Foo")
        self.assertIsNone(serializers.RecipeSerializer.get_last_brewed(recipe))

    def test_get_last_brewed_one_instance(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        self.assertEquals(serializers.RecipeSerializer.get_last_brewed(recipe),
                          datetime.date(2017, 4, 7))

    def test_get_last_brewed_multiple_instances(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2016, 4, 7))
        self.assertEquals(serializers.RecipeSerializer.get_last_brewed(recipe),
                          datetime.date(2017, 4, 7))

    def test_get_number_of_batches(self):
        recipe = models.Recipe.objects.create(name="Foo")
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2017, 4, 7))
        models.RecipeInstance.objects.create(recipe=recipe,
                                             date=datetime.date(2016, 4, 7))
        self.assertEquals(
            serializers.RecipeSerializer.get_number_of_batches(recipe), 2)
