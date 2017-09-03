"""Tests joulia.unit_conversions.
"""

from django.test import TestCase

from joulia import unit_conversions


class GramsToPoundsTest(TestCase):
    def test_grams_to_pounds(self):
        self.assertEquals(unit_conversions.grams_to_pounds(1000.0), 2.20462)
