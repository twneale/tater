from re import escape as e
from tater import Lexer, bygroups, include


class Lexer(Lexer):
    re_skip = r'\s+'
    dont_emit = [
        'String.Start', 'String.End',
        'Comment.Start', 'Comment.End',
        ]

    tokendefs = {
        'root': [
            ('Symbol', r'(:?\w+(:? \w+)*)'),
            include('miscellany'),
            include('operators'),
            include('metachars'),
            ],

        'miscellany': [
            ('Linebreak', r'\n'),
            ('Whitespace', r'\s+'),
            ],

        'operators': [
            ('Operator.Equals',    e(r'=')),
            ('Operator.Concat',    e(r',')),
            ('Operator.Semicolon', e(r';')),
            ('Operator.Pipe',      e(r'|')),
            ('Operator.Hyphen',    e(r'-')),
            ],

        'metachars': [
            ('Option.Start', e('[')),
            ('Option.End',   e(']')),
            ('Repeat.Start', e('{')),
            ('Repeat.End',   e('}')),
            ('Special',      e('?')),
            ('String.Start', '"', 'dqs'),
            ('String.Start', "'", 'sqs'),
            ('Comment.Start', e('(*'), 'comment'),
            ('Group.Start',   e('('), 'group'),
            ('Group.End',     e(')'), 'group'),
            ],

        'sqs': [
            ('String', "[^']+"),
            ('String.End', "'", '#pop'),
            ],

        'dqs': [
            ('String', '[^"]+'),
            ('String.End', '"', '#pop'),
            ],

        'comment': [
            (bygroups('Comment', 'Comment.End'), r'(.+?)(\*\))', '#pop'),
            ],
        }

