"""Utilities for generating random strings. Not to be considered
cyptographically safe.
"""

from os import urandom


def random_string(length, random_function=urandom):
    """Generates a string of ``length`` comprised of all random characters.

    Args:
        length: Length of the string to create.
        random_function: Function which can be called with a length argument
            and returns the provided number of bytes. Defaults to os.urandom.
    """
    byte_array = random_function(int(length / 2))
    integer = int.from_bytes(byte_array, byteorder='big')
    return '%04x' % integer
