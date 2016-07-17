#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('requirements.txt', 'r') as f:
    requirements = [line.rstrip() for line in f]

setup(
    name='joulia-webserver',
    install_requires=requirements,
    entry_points={
        'console_scripts': ['main = main:main']
    }
)