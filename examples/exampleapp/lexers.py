from tater import Lexer, bygroups, include


class Lexer(Lexer):
    re_skip = r'[\s,]+'
    dont_emit = ['Junk']

    tokendefs = {
        'root': [
            ('AreaCode', r'\(?\d{3}\)?', 'phone_number'),
            ],

        'phone_number': [
            ('Junk', r'\-'),
            ('PhoneNumber', r'\d{3}[- ]?\d{4}', 'extension'),
            ('Junk', r'ext\.?', 'extension'),
            ],

        'extension': [
            ('Extension', '\d+'),
            ]
        }

