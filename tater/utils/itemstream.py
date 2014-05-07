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
        if 5 <= len(self._stream):
            view += ' ...'
        cls_name = self.__class__.__name__
        return '%s(%s)' % (cls_name, view)

    def __len__(self):
        return len(self._stream._data)

    def __nonzero__(self):
        '''Return false if the stream is exhausted or if this iterator's
        index is equal to the length of the stream.
        '''
        return not self._stream._exhausted

    def done(self):
        return (len(self) - 1) == self.i

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
        try:
            return self._stream[self.i]
        except IndexError:
            raise StopIteration()

    def ahead(self, i, j=None):
        '''Raising stopiteration with end the parse.
        '''
        if j is None:
            return self._stream[self.i + i]
        else:
            return self._stream[self.i + i: self.i + j]

    def behind(self, n):
        return self._stream[self.i - n]

