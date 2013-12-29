import cPickle
import functools


class CachedAttr(object):
    '''Computes attr value and caches it in the instance.'''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


class CachedClassAttribute(object):
    '''Computes attribute value and caches it in class.

    Example:
        class MyClass(object):
            def myMethod(cls):
                # ...
            myMethod = CachedClassAttribute(myMethod)
    Use "del MyClass.myMethod" to clear cache.'''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        result = self.method(cls)
        setattr(cls, self.name, result)
        return result


class SetDefault(object):
    '''Context manager like getattr, but yields a default value,
    and sets on the instance on exit:

    with SetDefault(obj, attrname, []) as attr:
        attr.append('something')
    print obj.something
    '''
    def __init__(self, obj, attr, default_val):
        self.obj = obj
        self.attr = attr
        self.default_val = default_val

    def __enter__(self):
        val = getattr(self.obj, self.attr, self.default_val)
        self.val = val
        return val

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(self.obj, self.attr, self.val)


class DictSetDefault(object):
    '''Context manager like getattr, but yields a default value,
    and sets on the instance on exit:

    with DictSetDefault(somedict, key, []) as attr:
        attr.append('something')
    print obj['something']
    '''
    def __init__(self, obj, key, default_val):
        self.obj = obj
        self.key = key
        self.default_val = default_val

    def __enter__(self):
        val = self.obj.get(self.key, self.default_val)
        self.val = val
        return val

    def __exit__(self, exc_type, exc_value, traceback):
        self.obj[self.key] = self.val


class KeyClobberError(KeyError):
    pass


class NoClobberDict(dict):
    '''An otherwise ordinary dict that complains if you
    try to overwrite any existing keys.
    '''
    KeyClobberError = KeyClobberError
    def __setitem__(self, key, val):
        if key in self:
            msg = "Can't overwrite key %r in %r"
            raise KeyClobberError(msg % (key, self))
        else:
            dict.__setitem__(self, key, val)

    def update(self, otherdict=None, **kwargs):
        if otherdict is not None:
            dupes = set(otherdict) & set(self)
            for dupe in dupes:
                if self[dupe] != otherdict[dupe]:
                    msg = "Can't overwrite keys %r in %r"
                    raise KeyClobberError(msg % (dupes, self))
        if kwargs:
            for dupe in dupes:
                if self[dupe] != otherdict[dupe]:
                    msg = "Can't overwrite keys %r in %r"
                    raise KeyClobberError(msg % (dupes, self))
        dict.update(self, otherdict or {}, **kwargs)


def memoize_methodcalls(func, dumps=cPickle.dumps):
    '''Cache the results of the function for each input it gets called with.
    '''
    cache = func._memoize_cache = {}
    @functools.wraps(func)
    def memoizer(self, *args, **kwargs):
        key = dumps((args, kwargs))
        if args not in cache:
            cache[args] = func(self, *args, **kwargs)
        return cache[args]
    return memoizer


class IteratorWrapperBase(object):

    def __init__(self, iterator):
        self.iterator = iterator
        self.counter = 0

    def __iter__(self):
        while True:
            try:
                yield self.next()
            except StopIteration:
                return

    def next(self):
        return next(self.iterator)


class ListIteratorBase(list):

    def __init__(self, listy):
        self.listy = listy
        self.counter = 0

    def __iter__(self):
        while True:
            try:
                yield self.next()
            except StopIteration:
                return

    def next(self):
        try:
            val = self.listy[self.counter]
        except IndexError:
            raise StopIteration()
        try:
            return val
        finally:
            self.counter += 1


class LoopInterface(ListIteratorBase):
    '''A listy context manager wrapper that enables things like:

    listy = ['A', 'B', 'C']
    >>> with LoopInterface(listy) as loop:
    ... for thing in loop:
    ...     if loop.first:
    ...         pass
    ...     elif loop.last:
    ...         print ', and',
    ...     else:
    ...         print ',',
    ...     print thing, "(%s)" % loop.counter,
    ...     if loop.last:
    ...         print '.'
    >>> A (1) , B (2) , and C (3) .
    '''
    def __enter__(self):
        return self

    @property
    def first(self):
        return self.counter == 1

    @property
    def last(self):
        return self.counter == len(self.listy)

    @property
    def counter0(self):
        '''0-based loop counter.
        '''
        return self.counter - 1


class DictFilterMixin(object):
    '''
    listy = [dict(a=1), dict(a=2), dict(a=3)]
    for dicty in DictFilter(listy).filter(a=1):
        print dicty

    @dict_filter
    def
    '''
    def filter(self, **kwargs):
        '''Assumes all the dict's items are hashable.
        '''
        filter_items = set(kwargs.items())
        for dicty in self:
            dicty_items = set(dicty.items())
            if filter_items.issubset(dicty_items):
                yield dicty


class IteratorDictFilter(IteratorWrapperBase, DictFilterMixin):
    '''A dict filter that wraps an iterator.
    '''
    pass


def iterdict_filter(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        result = f(*args, **kwargs)
        return IteratorDictFilter(result)
    return wrapped
