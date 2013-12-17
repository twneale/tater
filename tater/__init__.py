# -*- coding: utf-8 -*-
"""Pythonic parsing framework"""
# :copyright: (c) 2009 - 2012 Thom Neale and individual contributors,
#                 All rights reserved.
# :license:   BSD (3 Clause), see LICENSE for more details.

from __future__ import absolute_import


VERSION = (0, 0, 2, '')
__version__ = '.'.join(str(p) for p in VERSION[0:3]) + ''.join(VERSION[3:])
__author__ = 'Thom Neale'
__contact__ = 'twneale@gmail.com'
__homepage__ = 'http://twneale.github.io/tater'
__docformat__ = 'restructuredtext'
__all__ = [
    'Lexer', 'DebugLexer', 'Token', 'include', 'bygroups', 'Rule',
    'Node', 'tokenseq', 'Scanner',
    '__version__']

# -eof meta-

from tater.base.node import *
from tater.base.visitor import *
from tater.base.lexer.utils import *

from tater.core.lexers import Lexer
from tater.core.parser import Parser
from tater.core.dispatchers import *
from tater.core.scanners import *
from tater.core import visitors
