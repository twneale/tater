# -*- coding: utf-8 -*-
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
import re
import json

from tater import new_basenode, tokenseq, token_subtypes
from tater import Lexer, Parser, bygroups, include


class JsonLexer(Lexer):

    re_skip = r'\s+'
    dont_emit = ('comma',)

    tokendefs = {
        'root': [
            ('Brace.Open', '\{', 'object'),
            ('Bracket.Open', '\[', 'array'),
            ],

        'object': [
            include('object.item'),
            ('Brace.Close', '\}', '#pop'),
            ],

        'object.item': [
            include('object.item.key'),
            ],

        'object.item.key': [
            (bygroups('Key'), r'"([^\\]+?)"\s*:', 'object.item.value'),
            ],

        'object.item.value': [
            include('root'),
            include('literals'),
            ('Comma', ',', '#pop'),
            ],

        'array': [
            include('array.item'),
            ('Bracket.Close', r'\]', '#pop'),
            ],

        'array.item': [
            include('root'),
            include('literals'),
            ('Comma', ','),
            ],

        'literals': [
            ('Literal.Number.Real', '\d+\.\d*'),
            ('Literal.Number.Int', '\d+'),
            (bygroups('Literal.String'), r'"((?:\\")?.+?[^\\])"'),
            ('Literal.Bool', '(?:true|false)'),
            ('Literal.Null', 'null'),
            ],
        }


Node = new_basenode()


class JsonRoot(Node):

    @tokenseq('Brace.Open')
    def start_object(self, *items):
        return self.descend_many('Object', 'ObjectItem')

    @tokenseq('Bracket.Open')
    def start_array(self, *items):
        return self.descend('Array')

    def decode(self):
        return next(iter(self)).decode()


class Value(JsonRoot):

    @token_subtypes('Literal')
    def handle_literal(self, *items):
        return self.descend('Literal', items).pop()


class Object(Node):

    @tokenseq('Comma')
    def end_item(self, *items):
        return self.descend('ObjectItem')

    @tokenseq('Brace.Close')
    def end_object(self, *items):
        return self.pop()

    def decode(self):
        res = {}
        for node in self:
            cow = list(node.decode())
            print cow
            k, v = cow
            res[k] = v
        return res
        return dict(node.decode() for node in self)


class ObjectItem(Node):

    @tokenseq('Key')
    def handle_key(self, *items):
        self.descend('ItemKey', items)
        return self.descend('ItemValue')

    def decode(self):
        for node in self:
            yield node.decode()


class ItemKey(Node):

    def decode(self):
        return self.first_text().decode('utf-8')


class ItemValue(Value):

    @token_subtypes('Literal')
    def handle_literal(self, *items):
        return self.descend('Literal', items).pop()

    def decode(self):
        for node in self:
            return node.decode()


class Array(Value):

    @tokenseq('Comma')
    def ignore_comma(self, *items):
        return self

    @tokenseq('Bracket.Close')
    def end_array(self, *items):
        return self.pop()

    def decode(self):
        return [node.decode() for node in self]


class Literal(Node):

    to_json = {
        'Literal.Number.Real': float,
        'Literal.Number.Int': int,
        'Literal.Bool': lambda s: s == 'true',
        'Literal.Null': lambda s: None,
        'Literal.String': lambda s: s.decode('utf-8')}

    def decode(self):
        first = self.first()
        func = self.to_json[first.token]
        return func(first.text)


def main():

    import pprint
    text = '''{
        "donkey": 1.23, "b": 3, "pig": true,
        "zip": null, "arr": [1, 2, "str"],
        "cow": '"pig\\'s"',
        "obj": {"a": 1}
        }'''

    import pdb; pdb.set_trace()
    for item in JsonLexer(text):
        print item

    parser = Parser(JsonLexer, JsonRoot, debug=True)
    tree = parser(text)
    decoded = tree.decode()

    assert json.loads(text) == decoded
    import pdb;pdb.set_trace()

if __name__ == '__main__':
    main()
