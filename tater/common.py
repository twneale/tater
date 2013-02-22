# -*- coding: utf-8 -*-
import re

from tater.node import Node, matches
from tater.tokentype import Token


re_enum = re.compile(r'\s*([\d\w\-\–\.]+)')
_divisions = u'''
    title
    tit.

    division
    div.

    paragraph
    par.

    section
    sec.

    part
    part.

    clause

    item

    chapter
    ch.
'''.split()
_divisions = _divisions + ['sub' + word for word in filter(None, _divisions)]
_divisions = _divisions + [word + 's' for word in filter(None, _divisions)]
_divisions = map(re.escape, _divisions)
_divisions = sorted(_divisions, key=len, reverse=True)
re_divisions = '(?i)\s*(%s)' % '|'.join(_divisions)


class HasSubdivisions(Node):
    '''This class can be mixed in to provide generic subdivisions
    path parsing.
    '''
    t = Token
    division_cls = None

    @matches(t.OpenParen, t.Division.PathEnum, t.CloseParen)
    def handle_subdiv(self, *items):
        open_paren, enum, close_paren = items
        child = self.descend(self.__class__, enum)

        # Regardless of depth, keep a reference to the top-level
        # section this subdivision belongs to.
        child.majornode = getattr(self, 'majornode', self)
        return child
