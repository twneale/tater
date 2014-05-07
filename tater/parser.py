import logging

from hercules import Token, Stream
from treebie import Node
from visitors import Visitor


class Parser(object):
    '''Chains lexer, Node, and arbitrary visitors together.
    '''
    def __init__(self, *classes, **options):
        self.classes = classes
        self.options = options

    def __call__(self, input_, **options):
        _options = self.options
        _options.update(options)
        for cls in self.classes:
            if issubclass(cls, Node):
                input_ = cls.parse(input_, **options)
            elif issubclass(cls, Visitor):
                input_ = cls().visit(input_)
            else:
                input_ = cls(input_, **options)
        return input_
