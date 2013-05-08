import inspect

from tater.core import ItemStream
from tater.utils import CachedAttr
from tater.utils.context import Context
from tater.tokentype import Token


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

        # Include all marked handlers in base classes in this
        # class's _funcs and _supertypes.
        _attrs = {}
        for base_attrs in map(get_attr_dict, bases):
            _attrs.update(base_attrs)

        # Now supercede the base attrs with this class def's attrs:
        _attrs.update(attrs)

        items = _attrs.items()

        # Sort the items if an order is given.
        order = _attrs.get('order')
        if order is not None:
            def sorter(item, order=order):
                attr, val = item
                if attr in order:
                    return order.index(attr)
                else:
                    return -1
            items.sort(sorter)

        for funcname, func in items:
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

    @property
    def edge_map(self):
        return getattr(self, '_edges', {})

    def first_token(self):
        return self.items[0][1]

    def first_text(self):
        return self.items[0][2]

    def resolve(self, itemstream):
        '''Try to resolve the incoming stream against the functions
        defined on the class instance.
        '''
        if not isinstance(itemstream, ItemStream):
            itemstream = ItemStream(itemstream)

        # Functions marked with 'matches' decorator.
        for func, tokens_or_items in self._funcs:
            items = itemstream.take_matching(tokens_or_items)
            if items:
                return func(self, *items)

        # Functions marked with 'matches_subtypes' decorator.
        # NOTE: it'd be way better if it just failed over to this method.
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
            msg = 'No function defined on %r for %s ...'
            i = itemstream.i
            stream = list(itemstream._stream)[i:i+10]
            raise ParseError(msg % (self, stream))

    def append(self, child, related=True, edge=None):
        '''Related is false when you don't want the child to become
        part of the resulting data structure, as in the case of the
        start node.
        '''
        if related:
            child.parent = self
            self.children.append(child)
            if edge is not None:
                self.edge_map[edge] = child
        return child

    def insert(self, index, child):
        '''Insert a child node a specific index.
        '''
        child.parent = self
        self.children.insert(index, child)
        return child

    def index(self):
        '''Return the index of this node in its parent's children
        list.
        '''
        parent = self.parent
        if parent is not None:
            return parent.children.index(self)

    def ascend(self, cls, items=None, related=True):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        items = items or []
        parent = cls(*items)
        parent.append(self, related)
        return parent

    def detatch(self):
        '''Remove this node from parent.
        '''
        self.parent.remove(self)
        return self

    def descend(self, cls, items=None, edge=None, transfer=False):
        items = items or []

        # Put single item into a list. This sucks.
        if items and isinstance(items[0], int):
            items = [items]

        child = cls(*items)
        if transfer:
            child.children.extend(self.children)
            self.children = []
        return self.append(child, edge=edge)

    def remove(self, child):
        'Um, should this return something? Not sure.'
        self.children.remove(child)

    def swap(self, cls, items=None):
        '''Swap cls(*items) for this node and make this node
        it's child.
        '''
        items = items or []
        new_parent = self.parent.descend(cls, items)
        self.parent.remove(self)
        new_parent.append(self)
        return new_parent

    def replace(self, cls_or_node, items=None, transfer=False):
        '''Replace this node wholesale with the specified child.
        Preserve order.
        '''
        items = items or []
        parent = self.parent
        children = parent.children
        index = children.index(self)

        # Remove this node.
        children.remove(self)

        if isinstance(cls_or_node, Node):
            # If a node was passed in, insert it.
            new_node = cls_or_node
        else:
            # Otherwise create a new node.
            cls = cls_or_node
            new_node = cls(*items)

        if transfer:
            new_node.children.extend(self.children)

        return parent.insert(index, new_node)

    def pop(self):
        '''Just for readability and clarity about what it means
        to return the parent.'''
        return self.parent

    def extend(self, *items):
        self.items.extend(items)
        return self

    def pprint(self, offset=0):
        print offset * ' ', '-', self
        for child in self.children:
            child.pprint(offset + 2)

    def pformat(self, offset=0, buf=None):
        buf = buf or []
        buf.extend([offset * ' ', '-', repr(self), '\n'])
        for child in self.children:
            child.pformat(offset + 2, buf)
        return ''.join(buf)

    @CachedAttr
    def context(self):
        try:
            return self._context
        except AttributeError:
            pass

        if hasattr(self, 'parent'):
            context = self.parent.context.new_child()
        else:
            context = Context()
        self._context = context
        return context

    def _depth_first(self):
        yield self
        for child in self.children:
            for node in child._depth_first():
                yield node

    # Querying methods.
    def has_siblings(self):
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return len(parent.children) > 1

    def following_siblings(self):
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return iter(parent.children[self.index()])

    def preceding_siblings(self):
        '''Iterate over preceding siblings from nearest to farthest.
        '''
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return reversed(parent.children[:self.index()])

    def preceding_sibling(self):
        try:
            return next(self.preceding_siblings())
        except StopIteration:
            return

    def find(self, type_):
        for node in self._depth_first():
            if isinstance(node, type_):
                yield node

    def find_one(self, type_):
        '''Find the only child matching the criteria.
        '''
        for node in self.find(type_):
            return node

    # Serialization methods.
    def as_data(self):
        items = []
        for (pos, token, text) in self.items:
            items.append((pos, token.as_json(), text))
        return dict(
            type=self.__class__.__name__,
            items=items,
            children=[child.as_data() for child in self.children]
            )

    @classmethod
    def fromdata(cls, data, namespace):
        '''
        namespace: is a dict containing all the required
        ast nodes to reconstitute this object.

        json_data: is the nested dict structure.
        '''
        node_cls = namespace[data['type']]
        items = []
        for pos, token, text in data['items']:
            items.append((pos, Token.fromstring(token), text))
        node = node_cls(*items)
        children = []
        for child in data['children']:
            children.append(cls.fromdata(child, namespace))
        node.children = children
        return node

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False

        # Don't care if the items are a list or tuple.
        if tuple(self.items) != tuple(other.items):
            return False

        if self.children != other.children:
            return False

        return True
