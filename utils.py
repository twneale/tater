from operator import itemgetter
from nose.tools import set_trace


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


class _TokenType(tuple):
    parent = None

    pos = property(itemgetter(0))
    tokentype = property(itemgetter(1))
    text = property(itemgetter(2))

    def split(self):
        buf = []
        node = self
        while node is not None:
            buf.append(node)
            node = node.parent
        buf.reverse()
        return buf

    def __init__(self, *args):
        # no need to call super.__init__
        self.subtypes = set()

    def __contains__(self, val):
        return self is val or (
            type(val) is self.__class__ and
            val[:len(self)] == self
        )

    def __getattr__(self, val):
        if not val or not val[0].isupper():
            return tuple.__getattribute__(self, val)
        new = self.__class__(self + (val,))
        setattr(self, val, new)
        self.subtypes.add(new)
        new.parent = self
        return new

    def __repr__(self):
        return 'Token' + (self and '.' or '') + '.'.join(self)


Token = _TokenType()


class Node(object):

    def __init__(self, name, key=None, value=None, parent=None,
                 attrs=None, kids=None):
        self.name = name
        attrs = attrs or {}
        if None not in [key, value]:
            attrs.update({key: value})
        self.attrs = attrs
        self.kids = kids or []
        self.parent = parent

    def __repr__(self):
        s = 'Node(name=%r, attrs=%r, kids=%r)'
        return s % (self.name, self.attrs, self.kids)

    def new_child(self, name, key, value):
        child = Node(name, key, value, parent=self)
        self.kids.append(child)
        return child

    def resolve(self, name, key, value):
        '''Refactor this crap.
        '''
        if name == self.name:
            if key in self.attrs:
                return self.parent.new_child(name, key, value)
            else:
                # Add the new data items to this instance.
                self.attrs.update({key: value})
                return self
        else:
            if self.kids:
                kid = self.kids[-1]
                if key in kid.attrs:
                    return self.new_child(name, key, value)
                else:
                    # Add the new data items to this instance.
                    kid.attrs.update({key: value})
                    return kid

            return self.new_child(name, key, value)

    def asdata(self):
        kids = [kid.asdata() for kid in self.kids]
        return dict(name=self.name, attrs=self.attrs, kids=kids)
