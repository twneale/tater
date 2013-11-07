from tater.utils.lazylist import LazyList


class ItemStream(object):
    '''A special iterator that wraps a lazy list and allows
    peeking and a more descriptive __repr__ method.
    '''
    def __init__(self, iterable):
        self._stream = LazyList(iterable)
        self.i = 0

    def __iter__(self):
        while True:
            try:
                yield self._stream[self.i]
            except IndexError:
                raise StopIteration
            self.i += 1

    def __repr__(self):
        items = tuple(self._stream[self.i: (self.i + 5)])
        view = repr(items)
        if 5 <= len(tuple):
            view + '...'
        return view

    def __len__(self):
        return len(self._stream)

    def __nonzero__(self):
        '''Return false if the stream is exhausted or if this iterator's
        index is equal to the length of the stream.
        '''
        if not self._stream._exhausted:
            if len(self) == self.i:
                return False
            return True
        else:
            return False

    def next(self):
        i = self.i
        try:
            item = self._stream[i]
        except IndexError:
            raise StopIteration
        else:
            self.i += 1
            return item

    # None of these methods advance the iterator. They're just
    # for peeking ahead and behind.
    def previous(self):
        return self.behind(1)

    def this(self):
        return self._stream[self.i]

    def ahead(self, i, j=None):
        '''Raising stopiteration with end the parse.
        '''
        if j is None:
            return self._stream[self.i + i]
        else:
            return self._stream[self.i + i: self.i + j]

    def behind(self, n):
        return self._stream[self.i - n]

