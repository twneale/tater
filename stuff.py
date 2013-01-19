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
            r(t.OfThe, 'of the', 'popular_name'),
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


#---------------------------------------------------------------------
# TODO:
# - Add debug, trace info
# - debug, get this POS working.
class ConfigurationError(Exception):
    '''The user-defined ast models were screwed up.
    '''


class ParseError(Exception):
    '''
    The tokens weren't matched against any suitable method
    on the current node.
    '''


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
        return self._stream[self.i + n]

    def behind(self, n):
        return self._stream[self.i - n]

    def take_matching(self, tokentypes_or_items):
        '''Take items from the stream matching the supplied
        sequence of tokentypes or (tokentype, text) 2-tuples.
        The imagined idiom here is pattern matching.
        '''
        tt = tokentypes_or_items

        # Return container for matched items.
        matched_items = []

        # Starting state of the iterator.
        offset = 0
        for tokentype_or_item in tokentypes_or_items:
            item = pos, tokentype, text = self.ahead(offset)
            match_found = False

            # Allow matching of a sequence of tokentypes.
            if isinstance(tokentype_or_item, _TokenType):
                if tokentype == tokentype_or_item:
                    print 'matched', tokentype_or_item
                    match_found = True
                    matched_items.append(item)

            # Alternatively, allow matching of a sequence of
            # (tokentype, text) 2-tuples.
            else:
                _item = _, _tokentype, _text = tokentype_or_item
                if (_tokentype, _text) == (tokentype, text):
                    match_found = True
                    print 'matched', _tokentype, _text
                    matched_items.append(item)

            if match_found:
                offset += 1

        if match_found:
            # Advance the iterator.
            self.i += len(matched_items)
            return matched_items


def parse(root_cls, itemiter):
    '''Supply a user-defined root class.
    '''
    itemstream = ItemStream(itemiter)
    node = root = root_cls()
    while 1:
        try:
            node = node.resolve(itemstream)
        except StopIteration:
            break
    return node.getroot()


def match(*tokentypes_or_items):
    '''Mark an instance method as suitable for
    resolving an incoming itemstream with items
    that matche tokens_or_items. It can match only
    the sequence of tokentypes, or it can match actual
    (tokentype, text) 2-tuples.
    '''
    if not tokentypes_or_items:
        msg = 'Supply at least one tokentype to match.'
        raise ConfigurationError(msg)

    def wrapped(f):
        f.tokentypes_or_items = tokentypes_or_items
        return f
    return wrapped


class NodeMeta(type):

    def __new__(meta, name, bases, attrs):
        funcs = []
        for funcname, func in attrs.items():
            tokentypes_or_items = getattr(func, 'tokentypes_or_items', None)
            if tokentypes_or_items:
                funcs.append((func, tokentypes_or_items))

        attrs.update(_funcs=funcs)
        cls = type.__new__(meta, name, bases, attrs)
        return cls


class Node(object):
    __metaclass__ = NodeMeta

    def __init__(self, *items):
        self.items = items
        self.children = []

    def getroot(self):
        this = self
        while hasattr(this, 'parent'):
            this = this.parent
        return this

    def resolve(self, itemstream):
        '''Try to resolve the incoming stream against the functions
        defined on the class instance.
        '''
        for func, tokentypes_or_items in self._funcs:
            items = itemstream.take_matching(tokentypes_or_items)
            if items:
                return func(self, *items)
        msg = 'No function defined on %r for %s'
        import ipdb;ipdb.set_trace()
        for func, tokentypes_or_items in self._funcs:
            items = itemstream.take_matching(tokentypes_or_items)
            if items:
                return func(self, *items)
        raise ParseError(msg % (self, repr(tokentypes_or_items)))

    def append(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def ascend(self, cls, items=None):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        items = items or []
        parent = cls(*items)
        parent.append(self)
        return parent

    def descend(self, cls, items=None):
        items = items or []
        child = cls(*items)
        return self.append(child)


class Start(Node):

    @match(t.Division.Name, t.Division.Enum)
    def division_name(self, *items):
        '''Create a division node with name, enum.
        '''
        return self.ascend(Division, items)


class Citations(Node):
    '''A root that multiple parallel citations can descend from.
    '''


class Division(Node):

    def __repr__(self):
        return 'Division(%r)' % (self.items,)

    @match(t.Of, t.Division.Name, t.Division.Enum)
    def handle_parent_div(self, *items):
        '''Create a new division(name, enum) and set it
        as the parent of self.
        '''
        return self.ascend(Division, items[1:])

    @match(t.OfThe, t.PopularName)
    def handle_popularname(self, *items):
        '''Set this node under an act.
        So ascend to a supernode.
        '''
        return self.ascend(PopularName, items)


class PopularName(Node):

    @match(t.Division.Title, t.USCode, t.Division.Enum)
    def handle_uscode_cite(self, *items):
        '''Ascend up to a new Citations node
        and descend back down into the US Code cite.
        '''
        title, usc, section = items

        citations = self.ascend(Citations)
        usc = citations.descend(USC, usc)
        title = usc.descend(Division, title)
        section = title.descend(Division, section)
        import ipdb;ipdb.set_trace()



class USC(Node):
    '''United States Code node (that rhymes)
    '''

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
    # s = 'Part D of title III of the Public Health Service Act (42 U.S.C. 254b et seq.)'
    print s
    items = list(ff.tokenize(s))
    pprint.pprint(items)
    import ipdb;ipdb.set_trace()
    parse(Start, items)

if __name__ == '__main__':
    main()
