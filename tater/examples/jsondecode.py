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
import re
import logging

from tater.node import Node, matches, matches_subtypes
from tater.core import RegexLexer, Rule, bygroups, parse, include
from tater.tokentype import Token


class Tokenizer(RegexLexer):
    #DEBUG = logging.FATAL

    re_skip = r'[,\s]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(t.OpenBrace, '{', 'object'),
            ],

        'literals': [
            r(t.Literal.Number.Real, '\d+\.\d*'),
            r(t.Literal.Number.Int, '\d+'),
            r(bygroups(t.Literal.String), r'"((?:\\")?.+?[^\\])"'),
            r(t.Literal.Bool, '(?:true|false)'),
            r(t.Literal.Null, 'null'),
            ],

        'object': [
            r(t.OpenBrace, '{', 'object'),
            r(t.OpenBracket, r'\[', push='array'),
            r(bygroups(t.KeyName), r'"([^\\]+?)"\s*:'),
            include('literals'),
            r(t.CloseBrace, '}', pop=True),
            ],

        'array': [
            include('literals'),
            r(t.CloseBracket, r'\]', pop=True),
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

    @matches_subtypes(t.Literal)
    def handle_literal(self, *items):
        return self.descend(JsonLiteral, items)


class JsonLiteral(Node):

    _to_json = {
        t.Literal.Number.Real: float,
        t.Literal.Number.Int: int,
        t.Literal.Bool: bool,
        t.Literal.Null: lambda x: None,
        t.Literal.String: lambda s: re.sub(r'\\"', '"', s).decode('utf-8'),
        }

    def decode(self):
        assert len(self.items) is 1
        _, token, text = self.items.pop()
        return self._to_json[token](text)


class JsonObject(Node):

    @matches(t.KeyName)
    def handle_keyname(self, *items):
        return self.descend(JsonObjectItem, items)

    @matches(t.CloseBrace)
    def end_object(self, *items):
        return self

    def decode(self):
        return dict(item.decode() for item in self.children)


class JsonObjectItem(Root):

    def decode(self):
        assert len(self.items) is 1
        _, _, key = self.items.pop()
        return (key, self.children.pop().decode())


class JsonArray(Root):

    @matches(t.CloseBracket)
    def end_array(self, *items):
        return self.parent

    def decode(self):
        return [expr.decode() for expr in self.children]


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
    data = x.decode()
    import ipdb;ipdb.set_trace()

if __name__ == '__main__':
    main()
