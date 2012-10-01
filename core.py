# -*- coding: utf8 -*-
import re
import itertools
from collections import defaultdict
from operator import methodcaller

from pygments.lexer import RegexLexer, bygroups
from pygments.token import *

import trie
from utils import CachedAttr

_translate_table = dict(zip(map(ord, ' .,:[]()'), itertools.repeat(None)))


def squish(u, tr_table=_translate_table):
    'Stupid name for a stupid function.'
    return u.translate(tr_table).lower()


class LexerType(type):

    _classes = set()

    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)
        meta._classes.add(cls)
        return cls

    @classmethod
    def classes(cls):
        return itertools.ifilterfalse(methodcaller('isabstract'), cls._classes)


class Scanner(object):

    @CachedAttr
    def _slug_regex(self):
        'A prematurely optimized prefix tree regex for locating cite slugs.'
        return trie.build_regex(cls.slug for cls in LexerType.classes())

    @CachedAttr
    def _slug_lexer_mapping(self):
        'Mapping of matched citation slugs to lexer classes.'
        return dict((squish(cls.slug), cls) for cls in LexerType.classes())

    def __call__(self, string):
        for matchobj in re.finditer(self._slug_regex, string, re.I):
            lexer = self._slug_lexer_mapping[squish(matchobj.group())]
            yield lexer().lex(matchobj, string)


class _SplitLexerBase(RegexLexer):
    'This modified RegexLexer bails after encountering an error token.'

    def get_tokens_unprocessed(self, text, Error=Token.Error):
        for pos, token, string in RegexLexer.get_tokens_unprocessed(self, text):
            if token == Error:
                return
            else:
                yield pos, token, string


class LexerBase(object):
    __metaclass__ = LexerType

    @classmethod
    def isabstract(cls):
        return not hasattr(cls, 'slug')

    @CachedAttr
    def reverse_lexer(self):
        class ReverseLexer(_SplitLexerBase):
            flags = re.U | re.M
            tokens = self.reverse_tokens
        return ReverseLexer()

    @CachedAttr
    def forward_lexer(self):
        class ForwardLexer(_SplitLexerBase):
            flags = re.U | re.M
            tokens = self.forward_tokens
        return ForwardLexer()

    def lex(self, matchobj, string, Junk=Token.Junk):

        result = defaultdict(list)

        rev_string = string[::-1][-matchobj.start():]
        rev_lexer = self.reverse_lexer
        rev_tokenized = list(rev_lexer.get_tokens_unprocessed(rev_string))
        for pos, token, text in rev_tokenized:
            if token != Junk:
                result[token].append(text[::-1])

        import pdb;pdb.set_trace()
        fwd_string = string[matchobj.end():]
        fwd_lexer = self.forward_lexer
        fwd_tokenized = list(fwd_lexer.get_tokens_unprocessed(fwd_string))
        for pos, token, text in fwd_tokenized:
            if token != Junk:
                result[token].append(text)
        return dict(result)


# Custom Tokens
Statute = Token.Statute
Junk = Token.Junk

# Regexes
rgxs = {
    'statute_section': '''
    (?x)                   # Compile verbose
    ,?\s{,2}               # Whitespace
    (\d[\w\-.]+)           # 123-2.1
    (?:\s{,2})             # Optional whitespace
    (\([\w\-.]+\))+        # Enumerations like "(1)" or "(12.1-a)"
    '''
    }


class Statute(LexerBase):

    reverse_tokens = {
        'root': [
            (ur'(\s*)(\d+)', bygroups(Junk, Statute.Title)),
            ]
        }

    forward_tokens = {
        'root': [
            (ur'(:?\s{,3})(:?\xa7{,2})*(?:\s{,3})%s' % rgxs['statute_section'],
                bygroups(Junk, Statute.SecSymbol, Statute.Section)),
            #(',?\s{,2}(\d[\w\-.]+)', bygroups(Statute.Section)),
            (ur'\s{,2}\((\d{4})(?:\)|(?: ed(?:\.?|ition),?))(?:\s{,2}Supp.? (\w+))?',
                bygroups(Statute.Edition, Statute.Supp)),
            (ur'(?:\s{,2}\([\w\-.]+\))+', Statute.Subdivisions)
            ],

        # 'subdivisions': [
        #     (ur'(?:\s{,2}\([\w\-.]+\))+', Statute.Subdivisions)
        #     ]
        }


class USC(Statute):
    slug = u'U.S.C.'


class CFR(Statute):
    slug = u'C.F.R.'


def main():
    import pdb;pdb.set_trace()
    scanner = Scanner()
    import pprint
    pprint.pprint(scanner._slug_lexer_mapping)
    ss = u"Blah blah blah 5 USC 123 blah blah 3 USC 4 and 12 CFR 23.4-1 sayus"
    print ss
    res = scanner(ss)
    pprint.pprint(list(res))
    # import pdb;pdb.set_trace()
if __name__ == '__main__':
    main()
