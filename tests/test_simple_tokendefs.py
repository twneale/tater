# -*- coding: utf-8 -*-
'''
Ultra simple HTML parser example.
'''
import logging
from unittest import TestCase
from tater import Lexer


class SimpleLexer(Lexer):
    re_skip = r'\s+'

    tokendefs = {
        'root': [
            ('number', '\d+'),
            ('lower', '[a-z]+'),
            ('pound', '#', 'test'),
            ],
        'test': [
            ('test_number', '\d+', '#pop'),
            ]
        }


class TestSimpleTokendefs(TestCase):

    text = '3 cows #4 pigs'

    expected = [
        (0, 1, 'number'),
        (2, 6, 'lower'),
        (7, 8, 'pound'),
        (8, 9, 'test_number'),
        (10, 14, 'lower')]

    def test_lexer(self):
        import nose.tools;nose.tools.set_trace()
        items = list(SimpleLexer(self.text, debug=True))
        items = map(tuple, items)
        self.assertEqual(items, self.expected)
