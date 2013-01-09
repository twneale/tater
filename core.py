# -*- coding: utf8 -*-
import re
import itertools
from collections import defaultdict, OrderedDict
from operator import methodcaller, itemgetter

from pygments.lexer import RegexLexer, bygroups
from pygments.token import *
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


class USC_Natural_Language(LexerBase):
    slug = u'United States Code'

    re_enumeration = ur'\s*(\d[\w\-.]+)'

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
    divisions = sorted((w[::-1] for w in divisions), key=len, reverse=True)
    re_divisions = '\s*(%s)' % '|'.join(divisions)

    reverse_tokens = {
        'root': [
            (ur'[\s,]*(\d+)', bygroups(t.Division.Enumeration)),
            (re_divisions, bygroups(t.Division.Name)),
            ]
        }

    forward_tokens = {
        'root': [
             ],

        # Things that are expected after a section number: subdivisions or
        # another section.
        'after_enum': [
            ]
        }

    def parse(self, rev_tokens, fwd_tokens):
        rev = self.flip_rev_tokens(rev_tokens)
        import nose.tools;nose.tools.set_trace()

    structure = yaml.load('''
        title:
          section:
            subdivisions:
        ''')



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
