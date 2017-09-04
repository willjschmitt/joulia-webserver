"""Django rest framework serializers for the brewery app.
"""
from rest_framework import serializers

from brewery import models


class JouliaControllerReleaseSerializers(serializers.ModelSerializer):
    """Standard serializer for JouliaControllerRelease model."""
    class Meta:
        model = models.JouliaControllerRelease
        fields = '__all__'


class BrewingCompanySerializer(serializers.ModelSerializer):
    """Standard serializer for BrewingCompany model."""
    class Meta:
        model = models.BrewingCompany
        fields = ('id', 'group', 'name',)


class BrewerySerializer(serializers.ModelSerializer):
    """Standard serializer for Brewery."""
    class Meta:
        model = models.Brewery
        fields = '__all__'


class ResistanceTemperatureDeviceSerializer(serializers.ModelSerializer):
    """Standard serializer for ResistanceTemperatureDevice."""
    class Meta:
        model = models.ResistanceTemperatureDevice
        fields = '__all__'


class ResistanceTemperatureDeviceAmplifierSerializer(serializers.ModelSerializer):
    """Standard serializer for ResistanceTemperatureDeviceAmplifier."""
    class Meta:
        model = models.ResistanceTemperatureDeviceAmplifier
        fields = '__all__'


class ResistanceTemperatureDeviceMeasurementSerializer(
        serializers.ModelSerializer):
    """Standard serializer for ResistanceTemperatureDeviceMeasurement."""
    rtd = ResistanceTemperatureDeviceSerializer()
    amplifier = ResistanceTemperatureDeviceAmplifierSerializer()

    class Meta:
        model = models.ResistanceTemperatureDeviceMeasurement
        fields = '__all__'

    def create(self, validated_data):
        validated_data['rtd'] = ResistanceTemperatureDeviceSerializer()\
            .create(validated_data.get('rtd', {}))
        validated_data['amplifier']\
            = ResistanceTemperatureDeviceAmplifierSerializer().create(
                validated_data.get('amplifier', {}))
        return models.ResistanceTemperatureDeviceMeasurement\
            .objects.create(**validated_data)

    def update(self, instance, validated_data):
        ResistanceTemperatureDeviceSerializer()\
            .update(instance.rtd, validated_data.pop('rtd', {}))
        ResistanceTemperatureDeviceAmplifierSerializer()\
            .update(instance.amplifier, validated_data.pop('amplifier', {}))
        return super(ResistanceTemperatureDeviceMeasurementSerializer, self)\
            .update(instance, validated_data)


class MashTunSerializer(serializers.ModelSerializer):
    """Standard serializer for MashTun."""
    temperature_sensor = ResistanceTemperatureDeviceMeasurementSerializer()

    class Meta:
        model = models.MashTun
        fields = '__all__'

    def create(self, validated_data):
        validated_data['temperature_sensor']\
            = ResistanceTemperatureDeviceMeasurementSerializer().create(
                validated_data.get('temperature_sensor', {}))
        return models.MashTun.objects.create(**validated_data)

    def update(self, instance, validated_data):
        ResistanceTemperatureDeviceMeasurementSerializer().update(
            instance.temperature_sensor,
            validated_data.pop('temperature_sensor', {}))
        return super(MashTunSerializer, self).update(
            instance, validated_data)


class HeatingElementSerializer(serializers.ModelSerializer):
    """Standard serializer for HeatingElement."""
    class Meta:
        model = models.HeatingElement
        fields = '__all__'


class HotLiquorTunSerializer(serializers.ModelSerializer):
    """Standard serializer for HotLiquorTun."""
    temperature_sensor = ResistanceTemperatureDeviceMeasurementSerializer()
    heating_element = HeatingElementSerializer()

    class Meta:
        model = models.HotLiquorTun
        fields = '__all__'

    def create(self, validated_data):
        validated_data['temperature_sensor']\
            = ResistanceTemperatureDeviceMeasurementSerializer().create(
                validated_data.get('temperature_sensor', {}))
        validated_data['heating_element'] = HeatingElementSerializer().create(
            validated_data.get('heating_element', {}))
        return models.HotLiquorTun.objects.create(**validated_data)

    def update(self, instance, validated_data):
        ResistanceTemperatureDeviceMeasurementSerializer().update(
            instance.temperature_sensor,
            validated_data.pop('temperature_sensor', {}))
        HeatingElementSerializer().update(
            instance.heating_element,
            validated_data.pop('heating_element', {}))
        return super(HotLiquorTunSerializer, self).update(
            instance, validated_data)


class PumpSerializer(serializers.ModelSerializer):
    """Standard serializer for Pump."""
    class Meta:
        model = models.Pump
        fields = '__all__'


class BrewhouseSerializer(serializers.ModelSerializer):
    """Standard serializer for Brewhouse. Makes use of writable nested
    serializers for equipment configuration."""
    active = serializers.ReadOnlyField()

    boil_kettle = HotLiquorTunSerializer()
    mash_tun = MashTunSerializer()
    main_pump = PumpSerializer()

    class Meta:
        model = models.Brewhouse
        fields = '__all__'

    def create(self, validated_data):
        validated_data['boil_kettle'] = HotLiquorTunSerializer().create(
            validated_data.get('boil_kettle', {}))
        validated_data['mash_tun'] = MashTunSerializer().create(
            validated_data.get('mash_tun', {}))
        validated_data['main_pump'] = PumpSerializer().create(
            validated_data.get('main_pump', {}))
        return models.Brewhouse.objects.create(**validated_data)

    def update(self, instance, validated_data):
        HotLiquorTunSerializer().update(
            instance.boil_kettle, validated_data.pop('boil_kettle', {}))
        MashTunSerializer().update(
            instance.mash_tun, validated_data.pop('mash_tun', {}))
        PumpSerializer().update(
            instance.main_pump, validated_data.pop('main_pump', {}))
        return super(BrewhouseSerializer, self).update(instance, validated_data)


class BeerStyleSerializer(serializers.ModelSerializer):
    """Standard serializer for BeerStyle."""
    class Meta:
        model = models.BeerStyle
        fields = '__all__'


class MaltIngredientSerializer(serializers.ModelSerializer):
    """Standard serializer for MaltIngredient."""
    class Meta:
        model = models.MaltIngredient
        fields = '__all__'


class BitteringIngredientSerializer(serializers.ModelSerializer):
    """Standard serializer for BitteringIngredient."""
    class Meta:
        model = models.BitteringIngredient
        fields = '__all__'


class MaltIngredientAdditionSerializer(serializers.ModelSerializer):
    """Standard serializer for MaltIngredientAddition."""
    class Meta:
        model = models.MaltIngredientAddition
        fields = '__all__'


class BitteringIngredientAdditionSerializer(serializers.ModelSerializer):
    """Standard serializer for BitteringIngredientAddition."""
    class Meta:
        model = models.BitteringIngredientAddition
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Standard serializer for Recipe."""
    last_brewed = serializers.SerializerMethodField()
    number_of_batches = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'style', 'last_brewed', 'number_of_batches',
                  'company', 'strike_temperature', 'mashout_temperature',
                  'mashout_time', 'boil_time', 'cool_temperature',
                  'original_gravity', 'ibu', 'srm', 'volume',)

    @staticmethod
    def get_last_brewed(recipe):
        recipe_instances = recipe.recipeinstance_set
        if recipe_instances.count() != 0:
            return recipe_instances.latest('date').date
        else:
            return None

    @staticmethod
    def get_number_of_batches(recipe):
        return recipe.recipeinstance_set.count()


class MashPointSerializer(serializers.ModelSerializer):
    """Standard serializer for MashPoint."""
    index = serializers.IntegerField(required=False)

    class Meta:
        model = models.MashPoint
        fields = '__all__'


class RecipeInstanceSerializer(serializers.ModelSerializer):
    """Standard serializer for RecipeInstance."""
    class Meta:
        model = models.RecipeInstance
        fields = '__all__'


class TimeSeriesDataPointSerializer(serializers.ModelSerializer):
    """Standard serializer for TimeSeriesDataPoint."""
    class Meta:
        model = models.TimeSeriesDataPoint
        fields = '__all__'
