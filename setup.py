#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='joulia-webserver',
    entry_points={
        'console_scripts': ['main = main:main']
    }
)