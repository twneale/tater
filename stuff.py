# -*- coding: utf-8 -*-
'''
Todo:
 - Handle weird unicode dashes.
 - May be helpful to yield the tokenizer state with
   the tokens.

'''
import re
import itertools
import collections
import ast
from operator import methodcaller, itemgetter
from ast import NodeVisitor, NodeTransformer, parse, dump, iter_child_nodes
from _ast import AST

from pygments.lexer import RegexLexer, RegexLexerMeta, bygroups
from pygments.token import *
from pygments.token import _TokenType

import uncompile
from utils import CachedAttr

_re_type = type(re.compile(''))
Rule = collections.namedtuple('Rule', 'tokentype rgxs push pop swap')


class Rule(Rule):
    'Rule(tokentype, rgxs, push, pop, swap)'

    def __new__(_cls, tokentype, rgxs,
        push=None, pop=None, swap=None):
        'Create new instance of Rule(tokentype, rgxs, push, pop, swap)'
        return tuple.__new__(_cls, (tokentype, rgxs, push, pop, swap))


def bygroups(*tokentypes):
    return tokentypes


class RegexLexer(object):
    '''We want a lexer that ignores whitespace, provides
    really detailed debug/trace and isn't fucking impossible
    to use. Tall order.
    '''
    # __metaclass__ = RegexLexerMeta
    DEBUG = True

    @CachedAttr
    def _tokendefs(self):
        '''Compile the tokendef regexes.
        '''
        # Make the patterns accessible on the lexer instance for debugging.
        rgx_pattern = self.rgx_pattern = {}

        iterable = collections.Iterable
        iter_rgxs = self.iter_rgxs

        flags = getattr(self, 'flags', 0)
        defs = collections.defaultdict(list)

        rubberstamp = lambda s: s
        re_compile = lambda s: re.compile(s, flags)
        getfunc = {
            unicode: re_compile,
            str: re_compile,
            _re_type: rubberstamp
            }

        for state, tokendefs in self.tokendefs.items():
            append = defs[state].append

            for tokendef in tokendefs:
                _rgxs = []
                _append = _rgxs.append

                for rgx, type_ in iter_rgxs(tokendef):
                    func = getfunc[type_](rgx)
                    rgx_pattern[func] = rgx
                    _append(func)

                rgxs = _rgxs
                tokendef = tokendef._replace(rgxs=rgxs)
                append(tokendef)

        return defs

    def iter_rgxs(self, rule, _re_type=_re_type):
        rgx = rgxs = rule.rgxs
        rgx_type = type(rgx)
        if issubclass(rgx_type, (basestring, _re_type)):
            yield rgx, rgx_type
        else:
            for rgx in rgxs:
                rgx_type = type(rgx)
                yield rgx, rgx_type

    # msg = "%r in rule %r wasn't re.compile'able."
        # raise TypeError(msg % (rgx, rule))


    def tokenize(self, text):
        '''Left off...something's whacked.
        '''
        DEBUG = self.DEBUG
        tokendefs = self._tokendefs
        statestack = ['root']
        defs = tokendefs['root']
        text_len = len(text)
        re_skip = re.compile(self.re_skip).match

        pos = 0
        while True:
            if DEBUG:
                print pos, statestack
            if text_len <= pos:
                return

            try:
                defs = tokendefs[statestack[-1]]
            except IndexError:
                defs = tokendefs['root']

            match_found = False
            stuff_skipped = False
            for tokentype, rgxs, push, pop, swap in defs:
                if DEBUG:
                    print '\n\nstring is', repr(text[pos:])
                    print ' --', tokentype, rgxs, push, pop, swap
                for rgx in rgxs:
                    if DEBUG:
                        print '  --regex', rgx.pattern
                    m = rgx.match(text, pos)
                    if not m:
                        # Skipper.
                        m = re_skip(text, pos)
                        if m:
                            stuff_skipped = True
                            pos = m.end()
                            continue
                    else:
                        match_found = True
                        if isinstance(tokentype, _TokenType):
                            yield pos, tokentype, m.group()
                        else:
                            matched = m.group()
                            for tokentype, tok in zip(tokentype, m.groups()):
                                yield pos + matched.index(tok), tokentype, tok
                        pos = m.end()

                        # State transition
                        if swap and not (push or pop):
                            statestack.pop()
                            statestack.append(swap)
                        else:
                            if pop:
                                if isinstance(pop, bool):
                                    statestack.pop()
                                elif isinstance(pop, int):
                                    for _ in range(pop):
                                        statestack.pop()
                            if push:
                                if isinstance(push, basestring):
                                    statestack.append(push)
                                else:
                                    for state in push:
                                        statestack.append(push)

            if not match_found:
                # If it didn't break, no match for this def.
                statestack.pop()
                if not statestack:
                    # We popped from the root state.
                    return
                    statestack = ['root']

                # Advance 1 chr.
                if not stuff_skipped:
                    pos += 1


class USBillTokenizer(RegexLexer):
    slug = u'United States Code'
    DEBUG = False

    re_enum = re.compile(ur'\s*([\d\w\-–.]+)', re.UNICODE)
    divisions = u'''
        title
        division
        paragraph
        section
        part
        clause
        item
        chapter
    '''.split()
    divisions = divisions + ['sub' + word for word in divisions]
    divisions = sorted(divisions, key=len, reverse=True)
    re_divisions = '(?i)\s*(%s)' % '|'.join(divisions)
    re_skip = r'[, ]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(Token.USCode, 'United States Code'),
            r(Token.Of, 'of'),
            r(bygroups(t.Division.Name), re_divisions, push='enum'),
            ],

        'enum': [
            r(bygroups(t.Division.Enum), re_enum, swap='after_top_enum'),
            ],

        'after_top_enum': [
            r(t.Punctuation.OpenParen, '\(', 'paren_enum'),
            r(t.Punctuation.OfThe, 'of the', 'popular_name'),
            ],

        'paren_enum': [
            r(bygroups(t.Division.PathEnum), re_enum),
            r(t.Punctuation.CloseParen, '\)', pop=True),
            ],

        'popular_name': [
            r(bygroups(t.PopularName), r'\s+([^(]+)(?: \()', swap='uscode_parened'),
            ],

        'uscode_parened': [
            r(bygroups(
                t.Division.Title,
                t.USCode),
              r'(\d+) (U\.S\.C\.)', swap='enum'),
            ],


        }




def main():

    import pprint
    ff = USBillTokenizer()
    # pprint.pprint(dict(ff._tokendefs))
    s = 'Section 1142(b) of title 10, United States Code, '
    s = (
        'Section 3686 of the Energy Employees '
        'Occupational Illness Compensation Program '
        'Act of 2000 (42 U.S.C. 7385s-15)')
    s = 'Section 41 of title 28, United States Code'
    s = 'Section 3(a)(2) of the Securities Act of 1933 (15 U.S.C. 77c(a)(2)) '
    s = 'Section 611(e)(2)(C) of the Individuals with Disabilities Education Act (20 U.S.C. 1411(e)(2)(C))'
    s = 'Part D of title III of the Public Health Service Act (42 U.S.C. 254b et seq.)'
    print s
    tt = ff.tokenize(s)
    for xx in tt:
        print xx
    # pprint.pprint(tt)
    import uncompile
    import ipdb;ipdb.set_trace()

if __name__ == '__main__':
    main()