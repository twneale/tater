# -*- coding: utf-8 -*-
from tater import Parser

from .lexers import Lexer
from .nodes import Root
# from .visitors import PhoneInfoVisitor


if __name__ == '__main__':
    parser = Parser(Lexer, Root)
    text = '''
(* a simple program syntax in EBNF *)
program = 'PROGRAM', white space, identifier, white space,\
          'BEGIN', white space,
           { assignment, ";", white space },
           'END.' ;
identifier = alphabetic character, { alphabetic character | digit } ;
number = [ "-" ], digit, { digit } ;
string = '"' , { all characters - '"' }, '"' ;
assignment = identifier , ":=" , ( number | identifier | string ) ;
alphabetic character = "A" | "B" | "C" | "D" | "E" | "F" | "G"
                     | "H" | "I" | "J" | "K" | "L" | "M" | "N"
                     | "O" | "P" | "Q" | "R" | "S" | "T" | "U"
                     | "V" | "W" | "X" | "Y" | "Z" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
white space = ? white space characters ? ;
all characters = ? all visible characters ? ;
'''
    # for item in Lexer(text):
    #     print item
    toks = list(Lexer(text))
    root = Root()
    try:
        data = root.parse(toks, debug=True)
    except Exception as exc:
        root.pprint()
        raise exc
    data = root.parse(toks, debug=True)
    print data