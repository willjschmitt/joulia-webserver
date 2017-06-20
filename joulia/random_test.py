"""Tests for joulia.random module.
"""

from django.test import TestCase

from joulia import random


class RandomStringTest(TestCase):
    """Tests for random_string function."""

    class RandIntStub(object):
        def __init__(self, byte_array):
            self.byte_array = byte_array
            self._index = -1

        def __call__(self, length):
            return self.byte_array

    def test_random_string(self):
        random_function = self.RandIntStub(b'\xab\x09')
        got = random.random_string(4, random_function)
        self.assertEquals(got, "ab09")
