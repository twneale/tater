from tater import Parser

from .lexers import Lexer
from .nodes import PhoneInfo
from .visitors import PhoneInfoVisitor


if __name__ == '__main__':
    parser = Parser(Lexer, PhoneInfo, PhoneInfoVisitor)
    data = parser('(415)-555-1234 ext. 12')
    print data