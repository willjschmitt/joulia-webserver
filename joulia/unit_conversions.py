"""Handles conversions between units.
"""

POUNDS_TO_GRAMS = 0.00220462
OUNCES_TO_POUNDS = 16.0


def grams_to_pounds(grams):
    """Converts provided grams into pounds.

    Returns: Converted value, in pounds.

    Args:
        grams: The value to convert from, in grams.
    """
    return grams * POUNDS_TO_GRAMS


def grams_to_ounces(grams):
    """Converts provided grams into ounces (1/16 of a pound).

    Returns: Converted value, in ounces.

    Args:
        grams: The value to convert from, in grams.
    """
    return grams * POUNDS_TO_GRAMS * OUNCES_TO_POUNDS
