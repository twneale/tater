# -*- coding: utf8 -*-
import re
import itertools
from collections import defaultdict, OrderedDict
from operator import methodcaller, itemgetter

from pygments.lexer import RegexLexer, RegexLexerMeta, bygroups
from pygments.token import *
from pygments.token import _TokenType
import yaml

import trie
from utils import CachedAttr, Node

_translate_table = dict(zip(map(ord, ' .,:[]()'), itertools.repeat(None)))


def squish(u, tr_table=_translate_table):
    'Stupid name for a stupid function.'
    # try:
    return u.translate(tr_table).lower()
    # except:
    #     import nose.tools;nose.tools.set_trace()


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
            lexer_cls = self._slug_lexer_mapping[squish(matchobj.group())]
            lexer = lexer_cls()
            yield lexer(matchobj, string)


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
    DEBUG = True

    def __init__(self):
        self._fieldsdata = defaultdict(list)
        fields = getattr(self, 'fields', [])
        for field in fields:
            for key in ('required', 'flat'):
                if getattr(field, key):
                    self._fieldsdata[key].append(field.name)
        self._fields = dict((field.name, field) for field in fields)

    def __call__(self, matchobj, string):
        matchobj, string = self.before_lex(matchobj, string)
        rev_tokens, fwd_tokens = self.lex(matchobj, string)
        result = self.parse(rev_tokens, fwd_tokens)
        result = self.after_lex(result)
        return result.asdata()

    def get_slug(self):
        return self.slug.replace(' ', '').replace('.', '').lower()

    def before_lex(self, matchobj, string):
        '''Pre-lex hook.
        '''
        return matchobj, string

    def after_lex(self, result):
        '''Post-lex hook.
        '''
        return result

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
        '''Produces a mapping of token types to pos, text 2-tuples.
        '''
        rev_string = string[::-1][-matchobj.start():]
        rev_lexer = self.reverse_lexer
        rev_tokenized = list(rev_lexer.get_tokens_unprocessed(rev_string))

        fwd_string = string[matchobj.end():]
        fwd_lexer = self.forward_lexer
        fwd_tokenized = list(fwd_lexer.get_tokens_unprocessed(fwd_string))

        if self.DEBUG:
            self.rev_string = self.rs = rev_string
            self.fwd_string = self.fs = fwd_string
            self.rev_tokenized = self.rt = rev_tokenized
            self.fwd_tokenized = self.ft = fwd_tokenized

        return (rev_tokenized, fwd_tokenized)

    def flip_rev_tokens(self, toks):
        '''Flip the rev tokens so they appear in natural left-to-right
        order.
        '''
        return [(pos, token, text[::-1]) for (pos, token, text) in toks[::-1]]

def scan(string, scanner=Scanner()):
    return scanner(string)


# Custom Tokens
Statute = Token.Statute
Junk = Token.Junk
t = Token


class Statute(LexerBase):

    reverse_tokens = {
        'root': [
            (ur'\s*(\d+)', bygroups(t.Title.Enumeration)),
            ]
        }

    re_enumeration = ur'\s*(\d[\w\-.]+)'

    forward_tokens = {
        'root': [
            (ur'\s*(\xa7{1,2})', bygroups(t.SecSymbol)),
            (re_enumeration, bygroups(t.Section.Enumeration), 'after_enum'),
            (ur'\s{,2}\((\d{4})(?:\)|(?: ed(?:\.?|ition),?))(?:\s{,2}Supp.? (\w+))?',
                bygroups(t.Root.Edition, t.Root.Supplement)),
            (ur', ', t.Junk),
            ],

        # Things that are expected after a section number: subdivisions or
        # another section.
        'after_enum': [
            (ur'(?i)\s{,2}(et\s{,5}seq\.?)', bygroups(t.Section.EtSeq)),
            (',\s*' + re_enumeration, bygroups(t.Section.Enumeration)),
            (ur'(?i)\s{,2}(note)\.', bygroups(t.Section.Note)),
            (ur'(?:\s{,2}\([\w\-.]+\))+', t.Section.Subdivisions, '#pop'),
            ('', Junk, '#pop')
            ]
        }

    structure = yaml.load('''
        title:
          section:
            subdivisions:
        ''')

    def _process_tokens(self, tokens, result, stack, parent_map, reverse=False):
        for pos, token, text in tokens:
            if reverse:
                text = text[::-1]
            node_name, value_name = str(token).lower().split('.')[-2:]

            # Skip if node_name isn't represented in the schema.
            if node_name != 'root' and node_name not in parent_map:
                continue

            # Get the node_name's parent name.
            parent_name = parent_map[node_name]

            # Get the last such node's parent from the stack.
            parent = stack[parent_name][-1]

            # Resolve our data against the retrieved parent.
            if node_name != 'root':
                node = parent.resolve(node_name, value_name, text)
                stack[node_name].append(node)
            else:
                node = result
                # Set the current text on the new node. Necessary?
                node.attrs[value_name] = text

        return result, stack

    def parse(self, rev_tokens, fwd_tokens):

        result = Node(name='root')
        stack = defaultdict(list)

        def _walk(node, parent_map=None, parent=None):
            '''Walk an arbitrarily nested dictionary
            and flatten it into a mapping of child keys
            to parent keys.
            '''
            if parent_map is None:
                parent_map = {'root': 'root'}
            if parent is None:
                parent = 'root'
            for key, val in node.items():
                parent_map[key] = parent
                if val:
                    _walk(val, parent_map, key)
            return parent_map

        parent_map = _walk(self.structure)
        stack['root'].append(result)

        rev_tokens = list(rev_tokens)
        result, stack = self._process_tokens(
            rev_tokens, result, stack, parent_map, reverse=True)
        fwd_tokens = list(fwd_tokens)
        result, stack = self._process_tokens(
            fwd_tokens, result, stack, parent_map)

        return result


class USC(Statute):
    slug = u'U.S.C.'


class PublicLaw(LexerBase):
    slug = u'publ'

    re_enumeration = ur'\s*(\d[\w\-.]+)'

    forward_tokens = {
        'root': [
            (ur'\s*(\xa7{1,2})', bygroups(t.SecSymbol)),
            (re_enumeration, bygroups(t.Section.Enumeration), 'after_enum'),
            (ur'\s{,2}\((\d{4})(?:\)|(?: ed(?:\.?|ition),?))(?:\s{,2}Supp.? (\w+))?',
                bygroups(t.Root.Edition, t.Root.Supplement)),
            (ur', ', t.Junk),
            ],

        # Things that are expected after a section number: subdivisions or
        # another section.
        'after_enum': [
            (ur'(?i)\s{,2}(et\s{,5}seq\.?)', bygroups(t.Section.EtSeq)),
            (',\s*' + re_enumeration, bygroups(t.Section.Enumeration)),
            (ur'(?i)\s{,2}(note)\.', bygroups(t.Section.Note)),
            (ur'(?:\s{,2}\([\w\-.]+\))+', t.Section.Subdivisions, '#pop'),
            ('', Junk, '#pop')
            ]
        }

    structure = yaml.load('''
        title:
          section:
            subdivisions:
        ''')


# class USC_Natural_Language(LexerBase):
#     slug = u'United States Code'

#     re_enumeration = ur'\s*(\d[\w\-.]+)'

#     divisions = u'''
#         title
#         division
#         paragraph
#         section
#         part
#         clause
#         item
#         chapter
#     '''.split()
#     divisions = divisions + ['sub' + word for word in divisions]
#     divisions = sorted((w[::-1] for w in divisions), key=len, reverse=True)
#     re_divisions = '\s*(%s)' % '|'.join(divisions)

#     reverse_tokens = {
#         'root': [
#             (ur'[\s,]*(\d+)( of)?', bygroups(t.Division.Enumeration)),
#             (re_divisions, bygroups(t.Division.Name)),
#             ]
#         }

#     forward_tokens = {
#         'root': [
#              ],

#         # Things that are expected after a section number: subdivisions or
#         # another section.
#         'after_enum': [
#             ]
#         }

#     def parse(self, rev_tokens, fwd_tokens):
#         rev = self.flip_rev_tokens(rev_tokens)
#         import nose.tools;nose.tools.set_trace()

#     structure = yaml.load('''
#         title:
#           section:
#             subdivisions:
#         ''')


class MyRegexLexer(RegexLexer):
    """
    Base for simple stateful regular expression-based lexers.
    Simplifies the lexing process so that you need only
    provide a list of states and regular expressions.
    """
    __metaclass__ = RegexLexerMeta

    #: Flags for compiling the regular expressions.
    #: Defaults to MULTILINE.
    flags = re.MULTILINE

    #: Dict of ``{'state': [(regex, tokentype, new_state), ...], ...}``
    #:
    #: The initial state is 'root'.
    #: ``new_state`` can be omitted to signify no state transition.
    #: If it is a string, the state is pushed on the stack and changed.
    #: If it is a tuple of strings, all states are pushed on the stack and
    #: the current state will be the topmost.
    #: It can also be ``combined('state1', 'state2', ...)``
    #: to signify a new, anonymous state combined from the rules of two
    #: or more existing ones.
    #: Furthermore, it can be '#pop' to signify going back one step in
    #: the state stack, or '#push' to push the current state on the stack
    #: again.
    #:
    #: The tuple can also be replaced with ``include('state')``, in which
    #: case the rules from the state named by the string are included in the
    #: current one.
    tokens = {}

    def get_tokens_unprocessed(self, text, stack=('root',)):
        """
        Split ``text`` into (tokentype, text) pairs.

        ``stack`` is the inital stack (default: ``['root']``)
        """
        pos = 0
        tokendefs = self._tokens
        statestack = list(stack)
        statetokens = tokendefs[statestack[-1]]
        re_white = re.compile(r'\s{1,10}').match
        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, pos)
                if m:
                    if type(action) is _TokenType:
                        yield pos, action, m.group()
                    else:
                        for item in action(self, m):
                            yield item
                    pos = m.end()
                    if new_state is not None:
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    statestack.pop()
                                elif state == '#push':
                                    statestack.append(statestack[-1])
                                else:
                                    statestack.append(state)
                        elif isinstance(new_state, int):
                            # pop
                            del statestack[new_state:]
                        elif new_state == '#push':
                            statestack.append(statestack[-1])
                        else:
                            assert False, "wrong state def: %r" % new_state
                        statetokens = tokendefs[statestack[-1]]
                    break
                else:
                    # Skip all whitespace not specified in lexer defs.
                    m = re_white(text, pos)
                    if m:
                        pos = m.end()
                        break

            else:
                try:
                    if text[pos] == '\n':
                        # at EOL, reset state to "root"
                        statestack = ['root']
                        statetokens = tokendefs['root']
                        yield pos, Text, u'\n'
                        pos += 1
                        continue
                    yield pos, Error, text[pos]
                    pos += 1
                except IndexError:
                    break


class Cow(MyRegexLexer):
    slug = u'United States Code'

    re_enumeration = ur'\s*([\d\w\-.]+)'

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

    tokens = {
        'root': [
            ('United States Code', Token.USCode),
            ('of', Token.Of, '#pop'),
            (re_divisions, bygroups(t.Division.Name), 'after_enum_type'),
            ],

        'after_enum_type': [
            (re_enumeration, bygroups(t.Division.Enumeration), 'after_top_enum'),
            ],

        'after_top_enum': [
            ('\(', t.Punctuation.OpenParen),
            (re_enumeration, bygroups(t.Division.PathEnum)),
            ('\)', t.Punctuation.CloseParen, ('#pop', 'root')),
            ],
        }

    # forward_tokens = {
    #     'root': [
    #          ],

    #     # Things that are expected after a section number: subdivisions or
    #     # another section.
    #     'after_enum': [
    #         ]
    #     }

    # def parse(self, rev_tokens, fwd_tokens):
    #     rev = self.flip_rev_tokens(rev_tokens)
    #     import nose.tools;nose.tools.set_trace()

    # structure = yaml.load('''
    #     title:
    #       section:
    #         subdivisions:
    #     ''')

def main():
    ff = Cow()
    tt = ff.get_tokens_unprocessed('Section 1142(b) of title 10, United States Code, ')
    tt = list(tt)
    import pprint
    pprint.pprint(tt)
    import pdb;pdb.set_trace()
    # scanner = Scanner()
    # import pprint
    # pprint.pprint(scanner._slug_lexer_mapping)
    # ss = u"Blah blah blah 5 USC 123 blah blah 3 USC 4 and 12 CFR 23.4-1 sayus"
    # print ss
    # res = scanner(ss)
    # pprint.pprint(list(res))
    # import pdb;pdb.set_trace()
if __name__ == '__main__':
    main()
