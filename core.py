# -*- coding: utf8 -*-
import re
import itertools
from collections import defaultdict, OrderedDict
from operator import methodcaller, itemgetter

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
        result = self.lex(matchobj, string)
        result = self.after_lex(matchobj, string, result)
        return result

    def get_slug(self):
        return self.slug.replace(' ', '').replace('.', '').lower()

    def before_lex(self, matchobj, string):
        '''Pre-lex hood.
        '''
        return matchobj, string

    def after_lex(self, matchobj, string, result):
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
        result = defaultdict(list)

        rev_string = string[::-1][-matchobj.start():]
        rev_lexer = self.reverse_lexer
        rev_tokenized = list(rev_lexer.get_tokens_unprocessed(rev_string))
        for pos, token, text in rev_tokenized:
            if token != Junk:
                result[token].append((pos, text[::-1]))

        fwd_string = string[matchobj.end():]
        fwd_lexer = self.forward_lexer
        fwd_tokenized = list(fwd_lexer.get_tokens_unprocessed(fwd_string))
        for pos, token, text in fwd_tokenized:
            if token != Junk:
                result[token].append((pos, text))
        return dict(result)


def scan(string, scanner=Scanner()):
    return list(scanner(string))


# Custom Tokens
Statute = Token.Statute
Junk = Token.Junk


class Statute(LexerBase):

    reverse_tokens = {
        'root': [
            (ur'\s*(\d+)', bygroups(Statute.Title)),
            ]
        }

    re_enumeration = ur'\s*(\d[\w\-.]+)'

    forward_tokens = {
        'root': [
            (ur'\s*(\xa7{1,2})', bygroups(Statute.SecSymbol)),
            (re_enumeration, bygroups(Statute.Section), 'after_enum'),
            (ur'\s{,2}\((\d{4})(?:\)|(?: ed(?:\.?|ition),?))(?:\s{,2}Supp.? (\w+))?',
                bygroups(Statute.Edition, Statute.Supplement)),
            (ur', ', Token.Junk),
            ],

        # Things that are expected after a section number: subdivisions or
        # another section.
        'after_enum': [
            (',\s*' + re_enumeration, bygroups(Statute.Section)),
            (ur'(?i)\s{,2}(note)\.', bygroups(Statute.Note)),
            (ur'(?i)\s{,2}(et\s{,5}seq)', bygroups(Statute.EtSeq)),
            (ur'(?:\s{,2}\([\w\-.]+\))+', Statute.Subdivisions, '#pop'),
            ('', Junk, '#pop')
            ]
        }

    def after_lex(self, matchobj, string, result):
        fields = self._fields
        default_field = Field('DefaultField')
        _result = result
        result = {}
        import nose.tools
        nose.tools.set_trace()
        for k, v in _result.items():
            new_k = str(k).split('.')[-1].lower()
            field = fields.get(new_k, default_field)
            value = None

            if field.boolean:
                result[new_k] = bool(text)
                continue
            elif field.flat is True:
                pos, value = v.pop()
            else:
                for pos, value in v:
                    pass

            result[new_k] = value

        result['id'] = self.get_slug()
        if 'subdivisions' in result:
            text = result['subdivisions']
            subs = text.strip(' ()')
            subs = re.split(r'\)\s*\(', subs)
            result['subdivisions'] = tuple(filter(None, subs))
        # import nose.tools
        # nose.tools.set_trace()

        return result

    def lex(self, matchobj, string, Junk=Token.Junk):
        '''Produces a mapping of token types to pos, text 2-tuples.
        '''
        rev_string = string[::-1][-matchobj.start():]
        rev_lexer = self.reverse_lexer
        rev_tokenized = list(rev_lexer.get_tokens_unprocessed(rev_string))

        fwd_string = string[matchobj.end():]
        fwd_lexer = self.forward_lexer
        fwd_tokenized = list(fwd_lexer.get_tokens_unprocessed(fwd_string))

        return (rev_tokenized, fwd_tokenized)

    t = Token
    rules = {
        'root': [
            rule(t.Literal, then='left_operand'),
            rule(t.Operator, ('+', '-',), then='unary_operator_left'),
            ],

        'left_operand': [
            rule(t.Operator, list('+-*/%'), then='binary_operator'),
            rule(t.Operator, ('++', '--'), then='unary_operator_left'),
            ],

        'binary_operator': [
            rule(t.Literal, then='right_operand'),
            rule(t.Punctuation, ('(')),
            rule(t.Operator, '+-', then='unary_operator_left'),
            ],

        'unary_operator_right': [
            rule(t.Operator, list('+-*/%'), then='binary_operator'),
            rule(t.Operator, ('+', '-', '++', '--'),
                 then='unary_operator_right'),
            rule(t.Punctuation, list(',;)'), end=True)
            ],

        'unary_operator_left': [
            rule(t.Literal, then='right_operand'),
            rule(t.Operator, list('+-'), then='unary_operator_left'),
            rule(t.Operator, ['++', '--'], then='unary_inc_dec_left'),
            ],

        'unary_inc_dec_left': [
            rule(t.Operator, ('+', '-', '++', '--'),
                 then='unary_operator_right'),
            rule(t.Punctuation, list(',;)'), end=True)
            ],

        'right_operand': [
            rule(t.Operator, list('+-*/%'), then='binary_operator'),
            rule(t.Operator, ('+', '-', '++', '--'),
                 then='unary_operator_right'),
            rule(t.Punctuation, list(',;)'), end=True)
            ]
        }



class Field(tuple):

    __slots__ = ()

    _fields = ('name', 'flat', 'required', 'groupwith',
               'boolean', 'kwargs')

    def __new__(_cls, name, flat=True, required=False,
                groupwith=None, boolean=False, **kwargs):
        return tuple.__new__(_cls, (name, flat, required, groupwith,
                                    boolean, kwargs))

    def __repr__(self):
        'Return a nicely formatted representation string'
        return ('Field(name=%r, flat=%r, required=%r, '
                'groupwith=%r, boolean=%r, kwargs=%r)') % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    __dict__ = property(_asdict)

    def _replace(_self, **kwds):
        'Return a new Field object replacing specified fields with new values'
        fields = ('name', 'flat', 'required', 'groupwith',
                  'boolean', 'kwargs')
        result = _self._make(map(kwds.pop, fields, _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    name = property(itemgetter(0), doc='Alias for field number 0')
    flat = property(itemgetter(1), doc='Alias for field number 1')
    required = property(itemgetter(2), doc='Alias for field number 2')
    groupwith = property(itemgetter(3), doc='Alias for field number 3')
    boolean = property(itemgetter(4), doc='Alias for field number 4')
    kwargs = property(itemgetter(4), doc='Alias for field number 5')


class USC(Statute):
    '''This is made weird by the need for a single scan result
    to find multiple section numbers--and for those sectios to
    share the id and title information.
    '''
    fields = (
        Field('title', required=True),
        Field('section', flat=False),
        Field('subdivisions', groupwith='section'),
        Field('note', boolean=True),
        Field('etseq', boolean=True),
        )

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
