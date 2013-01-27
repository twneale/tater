# -*- coding: utf-8 -*-
'''
Todo:
 - Handle weird unicode dashes.

'''
import re
import collections
import logging
import logging.config

from tater.config import LOGGING_CONFIG
from tater.tokentype import Token, _TokenType


logging.config.dictConfig(LOGGING_CONFIG)

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


class include(str):
    """
    Indicates that a state should include rules from another state.
    """
    pass


class _TokendefCompiler(object):

    def __init__(self, cls):
        self.cls = cls
        self.tokendefs = cls.tokendefs
        self.compiled = collections.defaultdict(list)

    def _process_rules(self, state, rules):

        flags = getattr(self.cls, 'flags', 0)

        rubberstamp = lambda s: s
        re_compile = lambda s: re.compile(s, flags)
        getfunc = {
                unicode: re_compile,
                str: re_compile,
                _re_type: rubberstamp
                }

        append = self.compiled[state].append
        iter_rgxs = self._iter_rgxs

        for rule in rules:
            if isinstance(rule, include):
                self._process_rules(state, self.tokendefs[rule])
                continue

            _rgxs = []
            _append = _rgxs.append

            for rgx, type_ in iter_rgxs(rule):
                func = getfunc[type_](rgx)
                _append(func)

            rgxs = _rgxs
            rule = rule._replace(rgxs=rgxs)
            append(rule)

    def compile_(self):
        '''Compile the tokendef regexes.
        '''
        for state, rules in self.tokendefs.items():
            self._process_rules(state, rules)
        return self.compiled

    def _iter_rgxs(self, rule, _re_type=_re_type):
        rgx = rgxs = rule.rgxs
        rgx_type = type(rgx)
        if issubclass(rgx_type, (basestring, _re_type)):
            yield rgx, rgx_type
        else:
            for rgx in rgxs:
                rgx_type = type(rgx)
                yield rgx, rgx_type


class RegexLexerMeta(type):

    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)
        if hasattr(cls, 'tokendefs'):
            cls._tokendefs = _TokendefCompiler(cls).compile_()
        return cls


class RegexLexer(object):
    '''We want a lexer that ignores whitespace, provides
    really detailed debug/trace and isn't fucking impossible
    to use.
    '''
    __metaclass__ = RegexLexerMeta

    DEBUG = logging.INFO

    class Finished(Exception):
        pass

    class MatchFound(Exception):
        pass

    def __init__(self):

        self._reset()

        if hasattr(self, 're_skip'):
            self.re_skip = re.compile(self.re_skip).match
        else:
            self.re_skip = None

        logger = logging.getLogger('tater.%s' % self.__class__.__name__)
        logger.setLevel(getattr(self, 'DEBUG', logging.FATAL))

        self.debug = logger.debug
        self.info = logger.info
        self.warn = logger.warn
        self.critical = logger.critical

    def _reset(self):
        self.pos = 0
        self.statestack = ['root']
        self.defs = self.tokendefs['root']
        self.text = None

    def tokenize(self, text):
        self._reset()
        self.info('Tokenizing text: %r' % text)
        self.text = text
        text_len = len(text)
        while True:
            # If here, we hit the end of the input. Stop.
            if text_len <= self.pos:
                return
            try:
                for item in self.scan():
                    self.info('  %r' % (item,))
                    yield item
            except self.Finished:
                return

    def scan(self):
        # Get the tokendefs for the current state.
        self.warn('  scan: text: %s' % self.text)
        self.warn('  scan:        ' + (' ' * self.pos) + '^')
        self.warn('  scan: pos = %r' % self.pos)
        try:
            defs = self._tokendefs[self.statestack[-1]]
            self.info('  scan: state is %r' % self.statestack[-1])
        except IndexError:
            defs = self._tokendefs['root']
            self.info("  scan: state is 'root'")

        try:
            for item in self._process_state(defs):
                yield item
        except self.MatchFound:
            self.debug('  _scan: match found--returning.')
            return

        msg = '  scan: match not found. Popping from %r.'
        self.info(msg % self.statestack)
        try:
            self.statestack.pop()
        except IndexError:
            raise self.Finished()

        if not self.statestack:
            self.debug('  scan: popping from root state; stopping.')
            # We popped from the root state.
            return

        # Advance 1 chr if we tried all the states on the stack.
        if not self.statestack:
            self.info('  scan: advancing 1 char.')
            self.pos += 1

    def _process_state(self, defs):
        if self.statestack:
            msg = ' _process_state: starting state %r'
            self.critical(msg % self.statestack[-1])
        for rule in defs:
            self.debug(' _process_state: starting rule %r' % (rule,))
            for item in self._process_rule(rule):
                yield item

    def _process_rule(self, rule):
        token, rgxs, push, pop, swap = rule

        pos_changed = False
        if self.re_skip:
            # Skipper.
            # Try matching the regexes before stripping,
            # in case they specify leading strippables.
            m = self.re_skip(self.text, self.pos)
            if m:
                self.info('  _process_rule: skipped %r' % m.group())
                msg = '  _process_rule: advancing pos from %r to %r'
                self.info(msg % (self.pos, m.end()))
                pos_changed = True
                self.pos = m.end()

        for rgx in rgxs:
            self.debug('  _process_rule: statestack: %r' % self.statestack)
            if pos_changed:
                self.info('  _process_rule: text: %r' % self.text)
                self.info('  _process_rule:        ' + (' ' * self.pos) + '^')
                pos_changed = False

            m = rgx.match(self.text, self.pos)
            self.debug('  _process_rule: trying regex %r' % rgx.pattern)
            if m:
                self.info('  _process_rule: match found: %s' % m.group())
                self.info('  _process_rule: pattern: %r' % rgx.pattern)
                if isinstance(token, _TokenType):
                    yield self.pos, token, m.group()
                else:
                    matched = m.group()
                    for token, tok in zip(token, m.groups()):
                        yield self.pos + matched.index(tok), token, tok

                msg = '  _process_rule: advancing pos from %r to %r'
                self.info(msg % (self.pos, m.end()))
                self.pos = m.end()
                self._update_state(rule)
                raise self.MatchFound()

    def _update_state(self, rule):
        token, rgxs, push, pop, swap = rule
        statestack = self.statestack

        # State transition
        if swap and not (push or pop):
            msg = '  _update_state: swapping current state for %r'
            self.info(msg % statestack[-1])
            statestack.pop()
            statestack.append(swap)
        else:
            if pop:
                if isinstance(pop, bool):
                    popped = statestack.pop()
                    self.info('  _update_state: popped %r' % popped)
                elif isinstance(pop, int):
                    self.info('  _update_state: popping %r states' % pop)
                    msg = '    _update_state: [%r] popped %r'
                    for i in range(pop):
                        popped = statestack.pop()
                        self.info(msg % (i, popped))

                # If it's a set, pop all that match.
                elif isinstance(pop, set):
                    self.info('  _update_state: popping all %r' % pop)
                    msg = '    _update_state: popped %r'
                    while statestack[-1] in pop:
                        popped = statestack.pop()
                        self.info(msg % (popped))

            if push:
                self.info('  _update_state: pushing %r' % (push,))
                if isinstance(push, basestring):
                    statestack.append(push)
                else:
                    self.info('  _update_state: pushing all %r' % (push,))
                    msg = '    _update_state: pushing %r'
                    for state in push:
                        self.info(msg % state)
                        statestack.append(state)


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
