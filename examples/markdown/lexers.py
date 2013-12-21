from tater import Lexer, bygroups, include


class Lexer(Lexer):

    tokendefs = {
        'root': [

            ('AngleBracket.Close', r'\>'),
            ('AngleBracket.Open', r'\<'),
            ('Paren.Open', r'\)'),
            ('Paren.Close', r'\('),
            ('Brace.Open', r'\}'),
            ('Brace.Close', r'\{'),
            ('Brace.Open', r'\]'),
            ('Brace.Close', r'\['),

            ('Quote.Double', r'"'),
            ('Quote.Single', r"'"),

            ('LineBreak', r'\n'),
            ('WhiteSpace', r'\s+'),
            ('Poundseq', r'#+'),
            ('Digits', r'\d+'),
            ('Dot', r'\.'),
            ('Letters', r'(?i)[a-z]+'),
            ('Symbol', r'[_=*$/|\-;]'),
            ('Colon', r':'),
            ],
        }

