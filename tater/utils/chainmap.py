## {{{ http://code.activestate.com/recipes/577434/ (r2)
'Nested contexts trees for implementing nested scopes (static or dynamic)'

from collections import MutableMapping
from itertools import chain, imap


class UsageError(Exception):
    '''Raised if the ChainMap is used wrong.
    '''
    pass

class ChainMap(MutableMapping):
    ''' Nested contexts -- a chain of mapping objects.
    Modified from activestate recipe so that ctx always resorts to
    its instance node's parent.ctx for chained lookups.

    Nonlocal behaviour and new_child were removed.
    '''
    def __init__(self, inst=None):
        'Create a new root context'
        self.map = {}
        if inst:
            self._inst = inst

    def __get__(self, inst, _type=None):
        self._inst = inst
        return self

    @property
    def inst(self):
        try:
            inst = self._inst
        except AttributeError:
            msg = (
                "This modified ChainMap descriptor only works when "
                "accessed as a class/instance attribute.")
            raise UsageError(msg)
        return inst

    @property
    def maps(self):
        yield self.map
        parent = getattr(self.inst, 'parent', None)
        if parent is None:
            return
        for m in parent.ctx.maps:
            yield m

    @property
    def root(self):
        'Return root context (highest level ancestor)'
        parent = getattr(self.inst, 'parent', None)
        return self if parent is None else parent.ctx.root

    def __getitem__(self, key):
        for m in self.maps:
            if key in m:
                break
        return m[key]

    def __setitem__(self, key, value):
        self.map[key] = value

    def __delitem__(self, key):
        del self.map[key]

    def __len__(self, len=len, sum=sum, imap=imap):
        return sum(imap(len, self.maps))

    def __iter__(self, chain_from_iterable=chain.from_iterable):
        return chain_from_iterable(self.maps)

    def __contains__(self, key, any=any):
        return any(key in m for m in self.maps)

    def __repr__(self, repr=repr):
        return ' -> '.join(imap(repr, self.maps))
