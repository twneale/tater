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
from tater.core import RegexLexer, Rule, bygroups, parse
from tater.tokentype import Token


class Tokenizer(RegexLexer):
    DEBUG = logging.DEBUG

    re_skip = r'[, ]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(t.OpenBrace, '{', 'object'),
            ],

        'object': [
            r(t.Number, '\d+\.?\d*'),
            r(t.DoubleQuote.Open, '"', push='keyname'),
            r(bygroups(t.String), r'(\\")?.+?[^\\]"'),
            r(t.OpenBrace, '}', pop=True),
            ],

        'keyname': [
            r(bygroups(t.Colon), r':', pop=True),
            r(bygroups(t.Keyname, t.DoubleQuote.End), r'([^\\]+?)(")'),
            ],
        }


t = Token


class Start(Node):

    @matches(t.OpenBrace)
    def start_object(self, *items):
        return self.ascend(JSONObject, items, related=False)


class ObjectItem(Node):

    @matches(t.String)
    def handle_string(self, *items):
        import ipdb;ipdb.set_trace()


class JSONObject(Node):

    @matches(t.DoubleQuote)
    def handle_dquote(self, *items):
        json_object = self.descend(JSONObject, items)
        object_item = ObjectItem()
        json_object.append(object_item)

        return object_item


def main():

    import pprint
    ff = Tokenizer()
    s = '{"donkey": 1.23, "b": 3, "cow": "\\"pig\'s\\""}'
    print s
    items = list(ff.tokenize(s))
    pprint.pprint(items)
    # x = parse(Start, items)
    # x.printnode()
    # import ipdb;ipdb.set_trace()

if __name__ == '__main__':
    main()

