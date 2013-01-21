# -*- coding: utf-8 -*-
'''
Todo:
 - Handle weird unicode dashes.

'''
import re
import collections

from tokentype import Token, _TokenType
from utils import CachedAttr


_re_type = type(re.compile(''))
Rule = collections.namedtuple('Rule', 'token rgxs push pop swap')


class Rule(Rule):
    'Rule(token, rgxs, push, pop, swap)'

    def __new__(_cls, token, rgxs,
        push=None, pop=None, swap=None):
        'Create new instance of Rule(token, rgxs, push, pop, swap)'
        return tuple.__new__(_cls, (token, rgxs, push, pop, swap))


def bygroups(*tokens):
    return tokens


class RegexLexer(object):
    '''We want a lexer that ignores whitespace, provides
    really detailed debug/trace and isn't fucking impossible
    to use. Tall order.
    '''
    DEBUG = True

    @CachedAttr
    def _tokendefs(self):
        '''Compile the tokendef regexes.
        '''
        # Make the patterns accessible on the lexer instance for debugging.
        rgx_pattern = self.rgx_pattern = {}

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

    def tokenize(self, text):
        DEBUG = self.DEBUG
        tokendefs = self._tokendefs
        statestack = ['root']
        defs = tokendefs['root']
        text_len = len(text)
        if hasattr(self, 're_skip'):
            re_skip = re.compile(self.re_skip).match
        else:
            re_skip = None

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
            for token, rgxs, push, pop, swap in defs:
                if DEBUG:
                    print '\n\nstring is', repr(text[pos:])
                    print ' --', token, rgxs, push, pop, swap
                for rgx in rgxs:
                    if DEBUG:
                        print '  --regex', rgx.pattern
                    m = rgx.match(text, pos)
                    if not m:
                        if re_skip:
                            # Skipper.
                            m = re_skip(text, pos)
                            if m:
                                stuff_skipped = True
                                pos = m.end()
                                continue
                    else:
                        match_found = True
                        if isinstance(token, _TokenType):
                            yield pos, token, m.group()
                        else:
                            matched = m.group()
                            for token, tok in zip(token, m.groups()):
                                yield pos + matched.index(tok), token, tok
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


t = Token


class ItemStream(object):

    def __init__(self, iterable):
        self._stream = list(iterable)
        self.i = 0

    def __iter__(self):
        while True:
            try:
                yield self._stream[self.i]
            except IndexError:
                raise StopIteration
            self.i += 1

    def next(self):
        i = self.i + 1
        try:
            item = self._stream[i]
        except IndexError:
            raise StopIteration
        else:
            self.i = i
            return item

    # None of these methods advance the iterator. They're just
    # for peeking ahead and behind.
    def previous(self):
        return self.behind(1)

    def this(self):
        return self._stream[self.i]

    def ahead(self, n):
        '''Raising stopiteration with end the parse.
        '''
        try:
            return self._stream[self.i + n]
        except IndexError:
            raise StopIteration

    def behind(self, n):
        return self._stream[self.i - n]

    def take_matching(self, tokens_or_items):
        '''Take items from the stream matching the supplied
        sequence of tokens or (token, text) 2-tuples.
        The imagined idiom here is pattern matching.
        '''
        # Return container for matched items.
        matched_items = []

        # Starting state of the iterator.
        offset = 0
        match_found = False
        for token_or_item in tokens_or_items:
            item = pos, token, text = self.ahead(offset)
            match_found = False

            # Allow matching of a sequence of tokens.
            if isinstance(token_or_item, _TokenType):
                if token == token_or_item:
                    match_found = True
                    matched_items.append(item)
                else:
                    break

            # Alternatively, allow matching of a sequence of
            # (token, text) 2-tuples.
            else:
                _, _token, _text = token_or_item
                if (_token, _text) == (token, text):
                    match_found = True
                    matched_items.append(item)

            if match_found:
                offset += 1

        if match_found:
            # Advance the iterator.
            self.i += len(matched_items)
            return matched_items


def parse(start, itemiter):
    '''Supply a user-defined start class.
    '''
    itemstream = ItemStream(itemiter)
    node = start()
    while 1:
        try:
            node = node.resolve(itemstream)
        except StopIteration:
            break
    return node.getroot()

