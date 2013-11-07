# -*- coding: utf-8 -*-
"""Pythonic parsing framework"""
# :copyright: (c) 2011 - 2013 Thom Neale and individual contributors,
#                 All rights reserved.
# :license:   BSD (3 Clause), see LICENSE for more details.

from __future__ import absolute_import

VERSION = (0, 0, 1, '')
__version__ = '.'.join(str(p) for p in VERSION[0:3]) + ''.join(VERSION[3:])
__author__ = 'Thom Neale'
__contact__ = 'twneale@gmail.com'
__homepage__ = 'http://twneale.github.io/tater'
__docformat__ = 'restructuredtext'
__all__ = [
    '__version__',

    # Lexing
    'Lexer', 'DebugLexer',
    'Token', 't', 'Rule', 'r',
    'include', 'bygroups',

    # Parsing
    'get_nodeclass', 'tokenseq', 'parse',

    # Visitors
    'Visitor', 'IteratorVisitor',
    'get_start', 'get_end', 'get_span']

# -eof meta-

import logging.config

from tater.core import config

from tater.base.node import *
from tater.base.lexer import *

from tater.core.parser import parse
from tater.core.visitors import *
from tater.core.tokentype import Token
from tater.core.dispatchers import *
