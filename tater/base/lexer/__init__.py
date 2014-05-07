import re
import sys
import logging
import functools

from tater.core.config import LOG_MSG_MAXWIDTH
from tater.core.tokentype import _TokenType

from tater.base.lexer import tokendefs
from tater.base.lexer.utils import include, bygroups, Rule
from tater.base.lexer.itemclass import get_itemclass
from tater.base.lexer.exceptions import IncompleteLex

from tater.utils import CachedAttr


__all__ = [
    'Lexer', 'DebugLexer', 'include', 'bygroups',
    'Rule', 'IncompleteLex']


class LexerMeta(type):
    '''Metaclass for the regular Lexer.
    '''
    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)
        if hasattr(cls, 'tokendefs'):
            cls._tokendefs = tokendefs.Compiler(cls).compile_all()
        return cls


class DebugLexerMeta(type):
    '''Metaclass for the DebugLexer.
    '''
    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)
        if hasattr(cls, 'tokendefs'):
            cls._tokendefs = tokendefs.DebugCompiler(cls).compile_all()
        return cls


class _LexerBase(object):
    pos = 0
    re_skip = None
    raise_incomplete = True
    dont_emit = []
    statestack = ['root']


class _RegularLexerBase(_LexerBase):
    '''Basic regex Lexer.
    '''
    __metaclass__ = LexerMeta

    def __init__(self, text, **kwargs):
        '''Text is the input string to lex. Pos is the
        position at which to start, or 0.
        '''
        self.text = text

        names = (
            'pos',
            're_skip',
            'raise_incomplete',
            'dont_emit',
            'statestack')

        for name in names:
            value = kwargs.get(name, getattr(self, name))
            setattr(self, name, value)


    def __iter__(self):
        return self.lex()

    def lex(self):

        pos = self.pos
        text = self.text
        Item = get_itemclass(text)
        statestack = self.statestack or ['root']
        tokendefs = self._tokendefs
        re_skip = self.re_skip
        text_len = len(text)
        dont_emit = self.dont_emit or []
        raise_incomplete = self.raise_incomplete

        if re_skip is not None:
            re_skip = re.compile(re_skip).match

        import pdb; pdb.set_trace()
        while True:
            if text_len <= pos:
                # If here, we hit the end of the input. Stop.
                return

            # Get this state's rules.
            try:
                defs = tokendefs[statestack[-1]]
            except IndexError:
                defs = tokendefs['root']

            break_state_loop = False
            while True:

                break_rule_loop = False
                for rule in defs:
                    if break_rule_loop:
                        break

                    token, rgxs, push, pop, swap = rule

                    if re_skip:
                        # Skipper.
                        # Try matching the regexes before stripping,
                        # in case they specify leading strippables.
                        m = re_skip(text, pos)
                        if m:
                            pos = m.end()

                    for rexmatch in rgxs:
                        m = rexmatch(text, pos)
                        if m:
                            if token in dont_emit:
                                pass
                            elif isinstance(token, (_TokenType, basestring)):
                                start, end = m.span()
                                yield Item(start, end, token)
                            else:
                                matched = m.group()
                                for token, (start, end) in zip(token, m.regs[1:]):
                                    assert start == pos + matched.index(text[start:end])
                                    yield Item(start, end, token)

                            # Advance the text offset.
                            pos = m.end()

                            # -------------------------------------------------
                            # Update state
                            # -------------------------------------------------
                            if swap and not (push or pop):
                                statestack.pop()
                                statestack.append(swap)
                            else:
                                if pop:
                                    if isinstance(pop, bool):
                                        statestack.pop()
                                    elif isinstance(pop, int):
                                        for i in range(pop):
                                            statestack.pop()

                                    # If it's a set, pop all that match.
                                    elif isinstance(pop, set):
                                        while statestack[-1] in pop:
                                            statestack.pop()

                                if push:
                                    if isinstance(push, basestring):
                                        if push == '#pop':
                                            statestack.pop()
                                        elif push.startswith('#pop:'):
                                            numpop = push.replace('#pop:', '')
                                            for i in range(numpop):
                                                statestack.pop()
                                        else:
                                            statestack.append(push)
                                    else:
                                        for state in push:
                                            statestack.append(state)

                            break_rule_loop = True
                            break_state_loop = True
                            break

                    if break_rule_loop:
                        break

                else:
                    # ---------------------------------------------------------
                    # No match found in this state.
                    # ---------------------------------------------------------
                    try:
                        statestack.pop()
                        # break
                    except IndexError:
                        # We're all out of states to try. Raise an error if the
                        # raise_incomplete is true.
                        if raise_incomplete:
                            raise IncompleteLex()

                    if not statestack:
                        # We popped from the root state.
                        if raise_incomplete:
                            raise IncompleteLex()

                if break_state_loop:
                    break


class _DebugLexerBase(_LexerBase):
    '''Extremely noisy debug version of the basic lexer.
    '''
    __metaclass__ = DebugLexerMeta

    class _Finished(Exception):
        pass

    class _MatchFound(Exception):
        pass

    def __init__(self, text, pos=None, statestack=None, **kwargs):
        '''Text is the input string to lex. Pos is the
        position at which to start, or 0.
        '''
        # Set initial state.
        self.text = text
        self.pos = pos or self.pos
        self.statestack = statestack or self.statestack[:]
        self.Item = get_itemclass(text)

        if self.re_skip is not None:
            self.re_skip = re.compile(self.re_skip).match

        loglevel = kwargs.get('loglevel', logging.DEBUG)
        def debug_func(func, debug=loglevel is not None,
                       log_msg_maxwidth=LOG_MSG_MAXWIDTH):
            @functools.wraps(func)
            def wrapped(msg):
                if debug:
                    func(msg[:log_msg_maxwidth])
            return wrapped

        logger = logging.getLogger('tater.%s' % self.__class__.__name__)
        logger.setLevel(loglevel)
        self.debug = debug_func(logger.debug)
        self.info = debug_func(logger.info)
        self.warn = debug_func(logger.warn)
        self.critical = debug_func(logger.critical)

    def __iter__(self):
        self.info('Tokenizing text: %r' % self.text)
        text_len = len(self.text)
        Item = self.Item
        while True:
            if text_len <= self.pos:
                # If here, we hit the end of the input. Stop.
                return
            try:
                for item in self.scan():
                    item = Item(*item)
                    self.warn('  %r' % (item,))
                    yield item
            except self._Finished:
                if text_len <= self.pos:
                    return
                elif self.raise_incomplete:
                    raise IncompleteLex()
                else:
                    return

    def scan(self):
        # Get the tokendefs for the current state.
        # self.warn('  scan: text: %s' % self.text)
        # self.warn('  scan:        ' + (' ' * self.pos) + '^')
        self.warn('  scan: %r' % self.text[self.pos:])
        self.warn('  scan: pos = %r' % self.pos)

        try:
            defs = self._tokendefs[self.statestack[-1]]
            self.info('  scan: state is %r' % self.statestack[-1])
        except IndexError:
            defs = self._tokendefs['root']
            self.info("  scan: state is 'root'")

        dont_emit = getattr(self, 'dont_emit', [])
        try:
            for start, end, token in self._process_state(defs):
                if token in dont_emit:
                    pass
                else:
                    yield start, end, token
        except self._MatchFound:
            self.debug('  _scan: match found--returning.')
            return

        msg = '  scan: match not found. Popping from %r.'
        self.info(msg % self.statestack)
        try:
            self.statestack.pop()
        except IndexError:
            self.debug('All out of states to process.Stopping.')
            raise self._Finished()

        if not self.statestack:
            self.debug('  scan: popping from root state; stopping.')
            # We popped from the root state.
            raise self._Finished()

        # # Advance 1 chr if we tried all the states on the stack.
        # if not self.statestack:
        #     self.info('  scan: advancing 1 char.')
        #     self.pos += 1

    def _process_state(self, defs):
        if self.statestack:
            msg = ' _process_state: starting state %r'
            self.critical(msg % self.statestack[-1])
            msg = ' _process_state: stack: %r'
            self.warn(msg % self.statestack)
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
                self.info('  _process_rule:        ' + (' ' * self.pos) + '^')
                pos_changed = False

            m = rgx.match(self.text, self.pos)
            self.debug('  _process_rule: trying regex %r' % rgx.pattern)
            if m:
                self.info('  _process_rule: match found: %s' % m.group())
                self.info('  _process_rule: pattern: %r' % rgx.pattern)
                if isinstance(token, (_TokenType, basestring)):
                    start, end = m.span()
                    yield start, end, token
                else:
                    matched = m.group()
                    for token, text in zip(token, m.groups()):
                        pos = self.pos + matched.index(text)
                        yield pos, pos + len(text), token

                msg = '  _process_rule: %r has length %r'
                self.info(msg % (m.group(), len(m.group())))
                msg = '  _process_rule: advancing pos from %r to %r'
                self.info(msg % (self.pos, m.end()))
                self.pos = m.end()
                self._update_state(rule)
                raise self._MatchFound()

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
                    if push == '#pop':
                        statestack.pop()
                    elif push.startswith('#pop:'):
                        numpop = push.replace('#pop:', '')
                        for i in range(numpop):
                            statestack.pop()
                    else:
                        statestack.append(push)
                else:
                    self.info('  _update_state: pushing all %r' % (push,))
                    msg = '    _update_state: pushing %r'
                    for state in push:
                        self.info(msg % state)
                        statestack.append(state)



