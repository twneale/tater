'''
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | unicode           |
    +---------------+-------------------+
    | number (int)  | int, long         |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+
'''

# -*- coding: utf-8 -*-
import logging

from tater.node import Node, matches
from tater.core import RegexLexer, Rule, bygroups, parse, include
from tater.tokentype import Token


class Tokenizer(RegexLexer):
    DEBUG = logging.DEBUG

    re_skip = r'[,\s]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(t.OpenBrace, '{', 'object'),
            ],

        'literals': [
            r(t.Number.Real, '\d+\.\d*'),
            r(t.Number.Int, '\d+'),
            r(t.String, r'"(?:\\")?.+?[^\\]"'),
            r(t.Bool, '(?:true|false)'),
            r(t.Null, 'null'),
            ],

        'object': [
            r(t.OpenBrace, '{', 'object'),
            r(bygroups(t.KeyName), r'"([^\\]+?)"\s*:'),
            include('literals'),
            r(t.OpenBracket, r'\[', push='array'),
            r(t.CloseBrace, '}', pop=True),
            ],

        'array': [
            include('literals'),
            r(t.CloseBracket, r'\]', pop=True),
            ],

        'keyname': [
            r(bygroups(t.Colon), r':', pop=True),
            r(bygroups(t.Keyname, t.DoubleQuote.End), r'([^\\]+?)(")'),
            ],
        }


t = Token


class Root(Node):

    @matches(t.OpenBracket)
    def start_array(self, *items):
        return self.descend(JsonArray)

    @matches(t.OpenBrace)
    def start_object(self, *items):
        return self.descend(JsonObject)

    @matches(t.String)
    @matches(t.Number.Int)
    @matches(t.Number.Real)
    @matches(t.Bool)
    @matches(t.Null)
    def handle_literal(self, *items):
        return self.descend(JsonLiteral, items)


class JsonLiteral(Node):
    pass


class JsonObject(Node):

    @matches(t.KeyName)
    def handle_keyname(self, *items):
        return self.descend(JsonObjectItem, items)

    @matches(t.CloseBrace)
    def end_object(self, *items):
        return self


class JsonObjectItem(Root):
    pass


class JsonArray(Root):

    @matches(t.CloseBracket)
    def end_array(self, *items):
        return self.parent


class Start(Node):

    @matches(t.OpenBrace)
    def start_object(self, *items):
        return self.ascend(JsonObject, related=False)


def main():

    import pprint
    ff = Tokenizer()
    s = '{"donkey": 1.23, "b": 3, "pig": true, "zip": null, "arr": [1, 2, "str"], "cow": "\\"pig\'s\\"", }'
    print s
    items = list(ff.tokenize(s))
    pprint.pprint(items)
    x = parse(Start, items)
    x.printnode()
    import ipdb;ipdb.set_trace()

if __name__ == '__main__':
    main()
