import re
import unittest

from tater import Token as t
from tater import Rule as r
from tater import Lexer
from tater.base.lexer.itemclass import get_itemclass


class TestLexer(Lexer):
    """Test tuple state transitions including #pop."""
    # DEBUG = logging.DEBUG
    re_skip = re.compile('\s+')
    tokendefs = {
        'root': [
            r(t.Root, 'a', push='bar'),
            r(t.Root, 'e'),
        ],
        'foo': [
            r(t.Foo, 'd', pop=2),
        ],
        'bar': [
            r(t.Bar, 'b', push='bar'),
            r(t.Bar, 'c', swap='foo'),
        ],
    }


class TupleTransTest(unittest.TestCase):
    text = 'abcde'
    Item = get_itemclass(text)

    expected = [
        Item(start=0, end=1, token=t.Root),
        Item(start=1, end=2, token=t.Bar),
        Item(start=2, end=3, token=t.Bar),
        Item(start=3, end=4, token=t.Foo),
        Item(start=4, end=5, token=t.Root)]

    def test(self):
        toks = list(TestLexer(self.text))
        self.assertEqual(toks, self.expected)
