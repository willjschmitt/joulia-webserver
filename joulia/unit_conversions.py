"""Handles conversions between units.
"""

POUNDS_TO_GRAMS = 0.00220462


def grams_to_pounds(grams):
    """Converts provided grams into pounds.

    Returns: Converted value, in pounds.

    Args:
        grams: The value to convert from, in grams.
    """
    return grams * POUNDS_TO_GRAMS
