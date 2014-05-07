import re
import json
import functools
from operator import itemgetter


class _PseudoMatch(object):
    '''A fake match object that provides the same basic interface
    as _sre.SRE_Match.'''

    def __init__(self, group, start, end, value):
        self._group = group
        self._start = start
        self._end = end
        self._value = value

    def group(self):
        return self._group

    def start(self):
        return self._start

    def end(self):
        return self._end

    def value(self):
        return self._value

    def _tuple(self):
        return (self._group, self._start, self._end, self._value)

    def __repr__(self):
        s = '_PseudoMatch(group=%r, start=%r, end=%r, value=%r)'
        return s % self._tuple()


class Trie(object):
    '''This trie needs to match a token sequence against a trie
    of tokentypes. Matches need to be returned as (value, substream)
    2-tuples.
    '''
    def __init__(self, trie=None, terminal_char=0, skipchars=None):
        self._trie = trie or {}
        self._terminal_char = terminal_char
        self._skipchars = skipchars or list(",. '&[]")

    def add(self, seq, value):
        terminal_char = self._terminal_char
        this = self._trie
        w_len = len(seq) - 1
        for i, c in enumerate(seq):
            if c in self._skipchars:
                continue
            try:
                this = this[c]
            except KeyError:
                this[c] = {}
                this = this[c]
            if i == w_len:
                this[terminal_char] = value

    def add_many(self, seq_value_2tuples):
        terminal_char = self._terminal_char
        trie = self._trie
        add = self.add
        for seq, value in seq_value_2tuples:
            add(seq, value, terminal_char)
        return trie

    def scan(self, itemstream, _match=_PseudoMatch, second=itemgetter(1)):
        res = []
        match = []
        this = trie = self._trie
        in_match = False
        terminal_char = self._terminal_char
        for item in itemstream:
            start, end, tokentype = item
            if tokentype in self._skipchars:
                if in_match:
                    match.append(item)
                continue
            if tokentype in this:
                this = this[tokentype]
                match.append(item)
                in_match = True
                if terminal_char in this:
                    _matchobj = _match(group=match,
                                       start=match[0][0], end=match[-1][0],
                                       value=this[terminal_char])
                    res.append(_matchobj)
            else:
                break

        if res:
            # The last match will always be the longest one.
            return res.pop()
        else:
            return []

    def dump(self, fp):
        s = json.dumps(self._trie)
        fp.write(s)

    def load(self, fp):
        self._trie = json.load(fp)

    @classmethod
    def from_jsonfile(cls, fp, *args, **kwargs):
        trie = cls(*args, **kwargs)
        trie.load(fp)
        return trie



class IncrementalTrie(object):

    def __init__(self, trie=None, terminal_char=0, skipchars=None):
        self._trie = trie or {}
        self._terminal_char = terminal_char
        self._skipchars = skipchars or list(",. '&[]")
        self.reset()

    def add(self, seq, value):
        terminal_char = self._terminal_char
        this = self._trie
        w_len = len(seq) - 1
        for i, c in enumerate(seq):
            if c in self._skipchars:
                continue
            try:
                this = this[c]
            except KeyError:
                this[c] = {}
                this = this[c]
            if i == w_len:
                this[terminal_char] = value

    def add_many(self, seq_value_2tuples):
        terminal_char = self._terminal_char
        trie = self._trie
        add = self.add
        for seq, value in seq_value_2tuples:
            add(seq, value, terminal_char)
        return trie

    def reset(self):
        self._this = self._trie
        self._in_match = False
        self._match = []
        self._res = []

    def process_token(self, item):
        pos, tokentype, text = item
        match = self._match

        if text in self._skipchars:
            if self._in_match:
                match.append(item)
            return self._in_match

        terminal_char = self._terminal_char
        this = self._this
        if text in this:
            this = self._this = this[text]
            match.append(item)
            self._in_match = True
            if terminal_char in this:
                matchobj = _PseudoMatch(
                    group=list(match),
                    start=match[0][0], end=match[-1][0],
                    value=this[terminal_char])
                self._res.append(matchobj)
                self._match = []
        else:
            self._in_match = False

        return self._in_match

    def get_result(self):
        result = self._res
        if result:
            return result

    def dump(self, fp):
        s = json.dumps(self._trie)
        fp.write(s)

    def load(self, fp):
        self._trie = json.load(fp)

    @classmethod
    def from_jsonfile(cls, fp, *args, **kwargs):
        trie = cls(*args, **kwargs)
        trie.load(fp)
        return trie
