# -*- coding: utf-8 -*-
'''
'''
import re
import logging

from tater.node import Node, matches, matches_subtypes
from tater.core import RegexLexer, Rule, bygroups, parse, include
from tater.tokentype import Token


class Tokenizer(RegexLexer):
    DEBUG = logging.DEBUG

    re_skip = r'[,\s]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            include('keywords'),
            include('expression'),
            include('data_structures'),
            r(t.OpenParen, r'\('),
            r(t.CloseParen, r'\)'),
            r(t.Semicolon, r';')
            ],

        'expression': [
            include('literals'),
            include('operators'),
            r(t.Function, 'function', 'func_sig'),
            r(t.Name, r'(?i)[a-z_][a-z_\d]*'),
            ],

        'keywords': [
            r(t.Keyword.Var, 'var'),
            r(bygroups(t.Assignment), '(=)[^=]?'),
            ],

        'operators': [
            r(t.BinOp.Mult, r'\*'),
            r(t.BinOp.Plus, r'\+'),
            r(t.BinOp.Minus, r'\-'),
            r(t.BinOp.Div, r'/'),
            ],

        'literals': [
            r(t.Literal.Number.Real, '\d+\.\d*'),
            r(t.Literal.Number.Int, '\d+'),
            r(bygroups(t.Literal.String), r'"((?:\\")?.+?[^\\])"'),
            r(t.Literal.Bool, '(?:true|false)'),
            r(t.Literal.Null, 'null'),
            ],

        'data_structures': [
            r(t.OpenBrace, r'{', 'object'),
            r(t.OpenBrace, r'\[', 'array'),
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

        'func_sig': [
            r(t.FuncSig.OpenParen, r'\('),
            r(t.FuncSig.CloseParen, r'\)\s+\{', push='function_body'),
            ],

        'function_body': [
            r(t.FuncBody.Begin, '\{', push='root'),
            r(t.FuncBody.End, '\}', pop=True)
            ]
        }


t = Token


class Expression(Node):

    @matches_subtypes(t.Literal)
    def handle_literal(self, *items):
        return self.descend(Value, items)

    @matches(t.Name)
    def handle_name(self, *items):
        return self.descend(Name, items)

    @matches(t.OpenParen)
    def handle_openparen(self, *items):
        return self.descend(Expression, items)

    @matches_subtypes(t.BinOp)
    def handle_binop(self, *items):
        return self.swap(BinOp, items)

    # These things make us exit the current expr state.
    @matches(t.Semicolon)
    def handle_sem(self, *items):
        parent = self.parent
        while isinstance(parent, Expression):
            parent = parent.parent
        return parent

    @matches(t.CloseParen)
    def handle_close_paren(self, *items):
        return self.pop()


class Value(Expression):
    pass


class Name(Value):

    @matches(t.Assignment)
    def handle_assigment(self, *items):
        new_parent = self.swap(Assignment)
        return new_parent.descend(Expression)


class Assignment(Expression):

    @matches_subtypes(t.Literal)
    def handle_literal(self, *items):
        return self.descend(Value, items)


class BinOp(Expression):
    pass


class Root(Node):

    @matches(t.Keyword.Var, t.Name)
    def handle_assign(self, *items):
        return self.descend(Name, items[1:])

    @matches(t.Name)
    def handle_assign_novar(self, *items):
        return self.descend(Name, *items)

    @matches(t.OpenBracket)
    def start_array(self, *items):
        return self.descend(Array)

    @matches(t.OpenBrace)
    def start_object(self, *items):
        return self.descend(Object)

    @matches(t.Semicolon)
    def handle_sem(self, *items):
        return self


# Data structures
class Object(Node):

    @matches(t.KeyName)
    def handle_keyname(self, *items):
        return self.descend(ObjectItem, items)

    @matches(t.CloseBrace)
    def end_object(self, *items):
        return self


class ObjectItem(Root):
    pass


class Array(Root):

    @matches(t.CloseBracket)
    def end_array(self, *items):
        return self.parent


def main():
    strings = [
        '''var x = 1; y = (1 + (x * 3));''',
        'var x = ((1 + 3) - 4) + 5',
        '''var cow  = function(a, b, c){return 1};''']

    for s in strings:
        import pprint
        ff = Tokenizer()
        print s
        items = list(ff.tokenize(s))
        pprint.pprint(items)
        print s
        x = parse(Root, items)
        x.printnode()

        import pdb;pdb.set_trace()

if __name__ == '__main__':
    main()
