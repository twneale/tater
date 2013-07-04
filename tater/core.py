# -*- coding: utf-8 -*-
'''
Todo:
 - Handle weird unicode dashes.

'''
import collections

from tater.tokentype import _TokenType


Rule = collections.namedtuple('Rule', 'token rgxs push pop swap')


class Rule(Rule):
    'Rule(token, rgxs, push, pop, swap)'

    def __new__(_cls, token, rgxs, push=None, pop=None, swap=None):
        'Create new instance of Rule(token, rgxs, push, pop, swap)'
        return tuple.__new__(_cls, (token, rgxs, push, pop, swap))


def bygroups(*tokens):
    return tokens


class include(str):
    """
    Indicates that a state should include rules from another state.
    """
    pass


class ItemIterator(object):
    '''Act like a list with getitem, but be lazy.
    '''
    def __init__(self, iterator):
        self.iterator = iterator
        self.i = 0
        self.data = []

    def __getitem__(self, int_or_slice):
        if isinstance(int_or_slice, slice):
            i = int_or_slice.stop
        else:
            i = int_or_slice

        data = self.data
        iterator = self.iterator

        # THIS IS FUCKED. Slice get's retured as if it's an int.
        if i and i < self.i:
            return data[i]

        while True:
            if i:
                if self.i <= i:
                    value = next(iterator)
                    data.append(value)
                    self.i += 1
                else:
                    break
            else:
                data.extend(list(iterator))
                self.i = len(self.data)
                break

        return data[int_or_slice]


class ItemStream(object):
    '''This is decent wrapper that makes an iterable act more like
    a list.
    '''

    def __init__(self, iterable):
        self._stream = ItemIterator(iter(iterable))
        self.i = 0

    def __iter__(self):
        while True:
            try:
                yield self._stream[self.i]
            except IndexError:
                raise StopIteration
            self.i += 1

    def __repr__(self):
        return repr(self._stream[self.i:][:5]) + '...'

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

        This should be separated into a mixin.
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
                _token, _text = token_or_item
                if (_token, _text) == (token, text):
                    match_found = True
                    matched_items.append(item)

            if match_found:
                offset += 1

        if match_found:
            # Advance the iterator.
            self.i += len(matched_items)
            return matched_items
