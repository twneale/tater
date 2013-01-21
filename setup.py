#!/usr/bin/env python

from setuptools import setup

long_description = """A reusable
"""

appname = "hy"
version = "0.7.5"

setup(**{
    "name": appname,
    "version": version,
    "packages": [
        'tater',
        ],
    "author": "Thom Neale",
    "author_email": "twneale@gmail.com",
    "long_description": long_description,
    "description": 'Tokenizer',
    "license": "MIT",
    "url": "http://tater.thomneale.com",
    "platforms": ['any'],
    "scripts": [
    ]
})
