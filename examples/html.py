# -*- coding: utf-8 -*-
'''
Ultra simple HTML parser example.
'''
import re

from tater import Node, matches#, matches_subtypes
from tater import Lexer, bygroups, parse, include

# Handle tokentypes behind the scenes!
class JsonLexer(Lexer):
    # import logging
    # DEBUG = logging.DEBUG

    re_skip = r'[,\s]+'

    tokendefs = {
        'root': [
            ('opentag', '<', 'tag'),
            ],

        'tag': [
            ()
            ]
        }


class Root(Node):

    @matches('opentag')
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
    s = '{"donkey": 1.23, "b": 3, "pig": true, "zip": null, "arr": [1, 2, "str"], "cow": "\\"pig\'s\\"" }'
    print s
    items = list(ff.tokenize(s))
    pprint.pprint(items)
    x = parse(Start, iter(items))
    x.printnode()
    data = x.decode()
    import json
    assert json.loads(s) == data
    import pdb;pdb.set_trace()

if __name__ == '__main__':
    main()
