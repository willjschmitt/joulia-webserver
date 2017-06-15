from django.db import models
from django.contrib.auth.models import User


class UserPreferences(models.Model):
    """Stores information associated with users for presentation layers.

    Attributes:
        user: User the preferences are associated with.
        energy_cost_rate: Unit price for energy where the user lives, for
            calculation of energy costs. Units: $/kWh.
    """

    user = models.OneToOneField(User)

    energy_cost_rate = models.FloatField(default=0.10)
