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


class KeyClobberError(KeyError):
    pass


class NoClobberDict(dict):
    '''An otherwise ordinary dict that complains if you
    try to overwrite any existing keys.
    '''
    def __setitem__(self, key, val):
        if key in self:
            msg = "Can't overwrite key %r in %r"
            raise KeyClobberError(msg % (key, self))
        else:
            dict.__setitem__(self, key, val)

    def update(self, otherdict=None, **kwargs):
        if otherdict is not None:
            dupes = set(otherdict) & set(self)
            if dupes:
                msg = "Can't overwrite keys %r in %r"
                raise KeyClobberError(msg % (dupes, self))
        if kwargs:
            dupes = set(kwargs) & set(self)
            if dupes:
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
