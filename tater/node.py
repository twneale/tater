import inspect


class ConfigurationError(Exception):
    '''The user-defined ast models were screwed up.
    '''


class ParseError(Exception):
    '''
    The tokens weren't matched against any suitable method
    on the current node.
    '''


def matches(*tokens_or_items):
    '''Mark an instance method as suitable for
    resolving an incoming itemstream with items
    that matche tokens_or_items. It can match only
    the sequence of tokens, or it can match actual
    (token, text) 2-tuples.
    '''
    if not tokens_or_items:
        msg = 'Supply at least one token to match.'
        raise ConfigurationError(msg)

    def wrapped(f):
        _tokens_or_items = getattr(f, 'tokens_or_items', [])
        _tokens_or_items.append(tokens_or_items)
        f.tokens_or_items = _tokens_or_items
        return f
    return wrapped


def matches_subtypes(*tokens):
    '''Mark an instance method as suitable for
    resolving an incoming itemstream with items
    having tokens that are subtypes of one or more
    passed-in tokens.
    '''
    if not tokens:
        msg = 'Supply at least one token to match.'
        raise ConfigurationError(msg)

    def wrapped(f):
        _tokens_supertypes = getattr(f, 'tokens_supertypes', [])
        _tokens_supertypes.extend(tokens)
        f._tokens_supertypes = _tokens_supertypes
        return f
    return wrapped


class _NodeMeta(type):

    def __new__(meta, name, bases, attrs):
        funcs = []

        # Can't think of a better name for this yet.
        supertypes = []

        get_attr_dict = lambda cls: dict(inspect.getmembers(cls))

        for attrs in map(get_attr_dict, bases) + [attrs]:
            for funcname, func in attrs.items():
                tokens_or_items = getattr(func, 'tokens_or_items', [])
                funcs.extend((func, data) for data in tokens_or_items)

                _supertypes = getattr(func, '_tokens_supertypes', [])
                supertypes.extend(
                    (func, _supertype) for _supertype in _supertypes)

        attrs.update(_funcs=funcs, _supertypes=supertypes)
        cls = type.__new__(meta, name, bases, attrs)
        return cls


class Node(object):
    __metaclass__ = _NodeMeta

    def __init__(self, *items):
        self.items = list(items)
        self.children = []

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.items,)

    def getroot(self):
        this = self
        while hasattr(this, 'parent'):
            this = this.parent
        return this

    def resolve(self, itemstream):
        '''Try to resolve the incoming stream against the functions
        defined on the class instance.
        '''
        # Functions marked with 'matches' decorator.
        for func, tokens_or_items in self._funcs:
            items = itemstream.take_matching(tokens_or_items)
            if items:
                return func(self, *items)

        # Functions marked with 'matches_subtypes' decorator.
        _, _token, _ = itemstream.this()
        for func, supertype in self._supertypes:
            if _token in supertype:
                items = itemstream.take_matching([_token])
                if items:
                    return func(self, *items)

        # No matched functions were found. Propagate up this node's parent.
        parent = getattr(self, 'parent', None)
        if parent is not None:
            return parent.resolve(itemstream)
        else:
            msg = 'No function defined on %r for %s'
            i = itemstream.i
            stream = itemstream._stream[i:i + 5] + ['...']
            raise ParseError(msg % (self, stream))

    def append(self, child, related=True):
        '''Related is false when you don't want the child to become
        part of the resulting data structure, as in the case of the
        start node.
        '''
        if related:
            child.parent = self
            self.children.append(child)
        return child

    def ascend(self, cls, items=None, related=True):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        items = items or []
        parent = cls(*items)
        parent.append(self, related)
        return parent

    def descend(self, cls, items=None):
        items = items or []
        child = cls(*items)
        return self.append(child)

    def extend(self, items):
        self.items.extend(items)
        return self

    def printnode(self, offset=0):
        print offset * ' ', '-', self
        for child in self.children:
            child.printnode(offset + 2)
