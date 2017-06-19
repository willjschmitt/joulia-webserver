from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserPreferences(models.Model):
    """Stores information associated with users for presentation layers.

    Attributes:
        user: User the preferences are associated with.
        energy_cost_rate: Unit price for energy where the user lives, for
            calculation of energy costs. Units: $/kWh.
    """

    user = models.OneToOneField(User)

    energy_cost_rate = models.FloatField(default=0.10)

    def __str__(self):
        return str(self.user) + " - User Preferences"


@receiver(post_save, sender=User)
def user_preferences_creator(sender, instance, **kwargs):
    """A django receiver watching for any saves on a User automatically create
    UserPreferences for it, if they do not exist yet.
    """
    try:
        instance.userpreferences
    except ObjectDoesNotExist:
        instance.userpreferences = UserPreferences.objects.create(
            user=instance)
