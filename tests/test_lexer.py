import re
import logging
import unittest

from tater.tokentype import Token as t
from tater.core import Rule as r
from tater.core import RegexLexer


class TestLexer(RegexLexer):
    """Test tuple state transitions including #pop."""
    DEBUG = logging.DEBUG
    re_skip = re.compile('\s+')
    tokendefs = {
        'root': [
            r(t.Root, 'a', push='rag'),
            r(t.Root, 'e'),
        ],
        'beer': [
            r(t.Beer, 'd', pop=2),
        ],
        'rag': [
            r(t.Rag, 'b', push='rag'),
            r(t.Rag, 'c', swap='beer'),
        ],
    }


class TupleTransTest(unittest.TestCase):
    def test(self):
        lx = TestLexer()
        toks = list(lx.tokenize('abcde'))
        self.assertEqual(toks,
           [(0, t.Root, 'a'), (1, t.Rag, 'b'), (2, t.Rag, 'c'),
            (3, t.Beer, 'd'), (4, t.Root, 'e')])
