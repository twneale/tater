#!/usr/bin/env python

from setuptools import setup

long_description = """Tokenizer and basic smart-objects
AST-builder implementation.
"""

appname = "tater"
version = "0.01"

setup(**{
    "name": appname,
    "version": version,
    "packages": [
        'tater',
        ],
    "author": "Thom Neale",
    "author_email": "twneale@gmail.com",
    "long_description": long_description,
    "description": 'Basic tokenizer and smart-objects implentation.',
    "license": "MIT",
    "url": "http://twneale.github.com/tater/",
    "platforms": ['any'],
    "scripts": [
    ]
})
