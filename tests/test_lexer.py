import re
import unittest

from rexlex import Lexer, Rule as r
from rexlex.lexer.itemclass import get_itemclass


class TestLexer(Lexer):
    """Test tuple state transitions including #pop."""
    # DEBUG = logging.DEBUG
    re_skip = re.compile('\s+')
    tokendefs = {
        'root': [
            r('Root', 'a', push='bar'),
            r('Root', 'e'),
        ],
        'foo': [
            r('Foo', 'd', pop=2),
        ],
        'bar': [
            r('Bar', 'b', push='bar'),
            r('Bar', 'c', swap='foo'),
        ],
    }


class TupleTransTest(unittest.TestCase):
    text = 'abcde'
    Item = get_itemclass(text)

    expected = [
        Item(start=0, end=1, token='Root'),
        Item(start=1, end=2, token='Bar'),
        Item(start=2, end=3, token='Bar'),
        Item(start=3, end=4, token='Foo'),
        Item(start=4, end=5, token='Root')]

    def test(self):
        toks = list(TestLexer(self.text))
        self.assertEqual(toks, self.expected)
