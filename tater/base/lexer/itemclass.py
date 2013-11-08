from operator import itemgetter
from collections import OrderedDict

from tater.utils import CachedAttr


class _ItemBase(tuple):
    '_ItemBase(start, end, token)'

    __slots__ = ()

    _fields = ('start', 'end', 'token')

    def __new__(_cls, start, end, token):
        'Create new instance of _ItemBase(start, end, token)'
        return tuple.__new__(_cls, (start, end, token))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new _ItemBase object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 3:
            raise TypeError('Expected 3 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        cls_name = self.__class__.__name__
        s = '%s(start=%%r, end=%%r, token=%%r, text=%%r)' % cls_name
        return s % (self + (self.text,))

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    __dict__ = property(_asdict)

    def _replace(_self, **kwds):
        'Return a new _ItemBase object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('start', 'end', 'token'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    start = property(itemgetter(0), doc='Alias for field number 0')
    end = property(itemgetter(1), doc='Alias for field number 1')
    token = property(itemgetter(2), doc='Alias for field number 2')

    @CachedAttr
    def text(self):
        '''Actually viewing an item's text is done lazying to avoid
        creating potentially unused strings.
        '''
        return self._text[self.start: self.end]


def get_itemclass(text, _ItemBase=_ItemBase):
    '''Return an _ItemBase subclass with the given text as a class attr.
    Enables the Item class to optimize speed and memory use by creating
    token text lazily.
    '''
    return type('Item', (_ItemBase,), dict(_text=text))
