import re
import unittest

<<<<<<< HEAD
from tater.tokentype import Token as t
from tater.core import Rule as r
from tater.lexer import RegexLexer


class TestLexer(RegexLexer):
=======
from tater import Token as t
from tater import Rule as r
from tater import Lexer
from tater.base.lexer.itemclass import get_itemclass


class TestLexer(Lexer):
>>>>>>> org
    """Test tuple state transitions including #pop."""
    # DEBUG = logging.DEBUG
    re_skip = re.compile('\s+')
    tokendefs = {
        'root': [
<<<<<<< HEAD
            r(t.Root, 'a', push='rag'),
            r(t.Root, 'e'),
        ],
        'beer': [
            r(t.Beer, 'd', pop=2),
        ],
        'rag': [
            r(t.Rag, 'b', push='rag'),
            r(t.Rag, 'c', swap='beer'),
=======
            r(t.Root, 'a', push='bar'),
            r(t.Root, 'e'),
        ],
        'foo': [
            r(t.Foo, 'd', pop=2),
        ],
        'bar': [
            r(t.Bar, 'b', push='bar'),
            r(t.Bar, 'c', swap='foo'),
>>>>>>> org
        ],
    }


class TupleTransTest(unittest.TestCase):
<<<<<<< HEAD
    def test(self):
        toks = list(TestLexer('abcde'))
        self.assertEqual(toks,
           [(0, t.Root, 'a'), (1, t.Rag, 'b'), (2, t.Rag, 'c'),
            (3, t.Beer, 'd'), (4, t.Root, 'e')])
=======
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
>>>>>>> org
