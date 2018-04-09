import logging

LOGGER = logging.getLogger(__name__)


def boil_volume_migrations(apps, _):
    """Sets default values on new boil volume fields.

    Recipe.pre_boil_volume_gallons and Recipe.post_boil_volume_gallons are
    defaulted to Recipe.volume for existing recipes.
    """
    Recipe = apps.get_model('brewery', 'Recipe')
    for recipe in Recipe.objects.all():
        recipe.pre_boil_volume_gallons = recipe.volume
        recipe.post_boil_volume_gallons = recipe.volume
        recipe.save()
