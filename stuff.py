import re
import itertools
import  collections
from operator import methodcaller, itemgetter

from pygments.lexer import RegexLexer, RegexLexerMeta, bygroups
from pygments.token import *
from pygments.token import _TokenType


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


class LexerState(object):
    'cow'


class RegexLexer(object):
    '''We want a lexer that ignores whitespace, provides
    really detailed debug/trace and isn't fucking impossible
    to use. Tall order.
    '''
    @CachedAttr
    def _tokendefs(self):
        '''Compile the tokendef regexes.
        '''
        iterable = collections.Iterable
        iter_rgxs = self.iter_rgxs

        flags = getattr(self, 'flags', 0)
        defs = collections.defaultdict(list)

        rubberstamp = lambda s: s
        re_compile = lambda s: re.compile(s, flags).match
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
                    _append(getfunc[type_](rgx))

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
        tokendefs = self._tokendefs
        statestack = ['root']
        defs = tokendefs['root']
        text_len = len(text)
        re_whitespace = re.compile(r'\s+').match

        pos = 0
        while True:
            print statestack
            if text_len < pos:
                return
            defs = tokendefs[statestack[-1]]

            match_found = False
            for tokentype, rgxs, push, pop, swap in defs:
                for rgxmatch in rgxs:
                    m = rgxmatch(text, pos)
                    if not m:
                        # Skip whitespace.
                        m = re_whitespace(text, pos)
                        if m:
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
                        if swap and not push or pop:
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

                        import ipdb;ipdb.set_trace()
            if not match_found:
                # If it didn't break, no match for this def.
                statestack.pop()
                if not statestack:
                    # We popped from the root state.
                    statestack = ['root']

                # Advance 1 chr.
                pos += 1


class Cow(RegexLexer):
    slug = u'United States Code'

    re_enum = ur'\s*([\d\w\-.]+)'

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

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(Token.USCode, 'United States Code'),
            r(Token.Of, 'of'),
            r(bygroups(t.Division.Name), re_divisions, 'after_enum_type'),
            ],

        'after_enum_type': [
            r(bygroups(t.Division.Enum), re_enum, 'after_top_enum'),
            ],

        'after_top_enum': [
            r(t.Punctuation.OpenParen, '\('),
            r(bygroups(t.Division.PathEnum), re_enum),
            r(t.Punctuation.CloseParen, '\)'),
            ],
        }


def main():
    import pprint
    ff = Cow()
    # pprint.pprint(dict(ff._tokendefs))
    s = 'Section 1142(b) of title 10, United States Code, '
    print s
    tt = ff.tokenize(s)
    for xx in tt:
        print xx
    # pprint.pprint(tt)
    import pdb;pdb.set_trace()

if __name__ == '__main__':
    main()