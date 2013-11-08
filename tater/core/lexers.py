import logging

from tater.core import config
from tater.base.lexer import _RegularLexerBase, _DebugLexerBase, tokendefs
from tater.base.lexer.exceptions import ConfigurationError
from tater.utils import CachedClassAttribute


class Lexer(object):

    pos = 0
    re_skip = None
    raise_incomplete = True
    dont_emit = []
    statestack = ['root']

    def __init__(self, *args, **kwargs):
        self.args = args
        self.config = config
        if not hasattr(self, 'tokendefs'):
            msg = "Lexer subclasses must have a top level 'tokendefs' attribute."
            raise ConfigurationError(msg)
        self.kwargs = kwargs

    @CachedClassAttribute
    def regular_lexer(cls):
        return type(cls.__name__, (_RegularLexerBase,), dict(cls.__dict__))

    @CachedClassAttribute
    def debug_lexer(cls):
        return type(cls.__name__, (_DebugLexerBase,), dict(cls.__dict__))

    def __iter__(self):

        # Figure out whether to use the debug lexer or not.
        loglevel = self.kwargs.get('loglevel')
        loglevel = loglevel or getattr(self.config, 'LOGLEVEL')
        if self.kwargs.get('debug'):
            loglevel = logging.DEBUG

        if loglevel is None:
            return iter(self.regular_lexer(*self.args, **self.kwargs))
        else:
            self.kwargs.update(loglevel=loglevel)
            return iter(self.debug_lexer(*self.args, **self.kwargs))

