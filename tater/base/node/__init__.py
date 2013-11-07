import uuid
import types
import inspect
from collections import defaultdict

from tater.core.tokentype import Token

from tater.utils import (
        CachedAttr, NoClobberDict, KeyClobberError, memoize_methodcalls)
from tater.utils.chainmap import ChainMap
from tater.utils.itemstream import ItemStream

from tater.base.node.nodespace import NodeSpace
from tater.base.node.resolvers import (
    MetaclassRegistryResolver, LazyImportResolver, LazyTypeCreator)


matches = 1
matches_subtypes = 2


class ConfigurationError(Exception):
    '''The user-defined ast models were screwed up.
    '''


class ParseError(Exception):
    '''
    The tokens weren't matched against any suitable method
    on the current node.
    '''


class _NodeMeta(type):

    @classmethod
    def get_base_attrs(meta, bases):
        '''Aggregate registered handlers from the node's base
        classes into the instance's dict.
        '''
        attrs = {}
        get_attr_dict = lambda cls: dict(inspect.getmembers(cls))
        for base_attrs in map(get_attr_dict, bases):
            attrs.update(base_attrs)
        return attrs

    @classmethod
    def get_sorted_attrs(meta, attrs):
        '''Sort the items if an order is given.
        '''
        items = attrs.items()
        order = attrs.get('order')
        if order is not None:
            def sorter(item, order=order):
                attr, val = item
                if attr in order:
                    return order.index(attr)
                else:
                    return -1
            items.sort(sorter)
        return items

    @classmethod
    def compile_dispatch_data(meta, items):
        dispatch_data = defaultdict(NoClobberDict)
        for _, method in items:
            disp = getattr(method, '_disp', None)
            if disp is None:
                continue
            for dispatcher, signature_dict in disp.items():
                for signature, method in signature_dict.items():
                    dispatch_data[dispatcher][signature] = method
        return dispatch_data

    @classmethod
    def prepare(meta, dispatch_data):
        '''Delegate further preparation of dispatch data to the
        dispatchers used on this class.
        '''
        res = {}
        for dispatcher, signature_dict in dispatch_data.items():
            res[dispatcher] = dispatcher.prepare(signature_dict)
        return res

    def __new__(meta, name, bases, attrs):
        # Merge all handlers registered on base classes into
        # this instance.
        _attrs = dict(attrs)
        _attrs.update(meta.get_base_attrs(bases))

        # Get them into the order specified on the class, if any.
        items = meta.get_sorted_attrs(_attrs)

        # Aggregate all the handlers defined on this class.
        dispatch_data = meta.compile_dispatch_data(items)
        dispatch_data = meta.prepare(dispatch_data)

        # Compile the class's noderef resolvers.
        if 'nodespace' in _attrs:
            nodespace = _attrs['nodespace']
            nodespace.add_resolvers(*_attrs['noderef_resolvers'])
            attrs['nodespace'] = nodespace

        # Update the class with the dispatch data.
        attrs.update(_dispatch_data=dispatch_data)
        cls = type.__new__(meta, name, bases, attrs)

        # Update the class's nodespace.
        if 'nodespace' in _attrs:
            cls.nodespace.register(cls)

        return cls


class Node(object):
    __metaclass__ = _NodeMeta

    nodespace = NodeSpace()
    noderef_resolvers = (
        MetaclassRegistryResolver,
        LazyImportResolver,
        LazyTypeCreator)

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

    @memoize_methodcalls
    def resolve_noderef(self, ref):
        '''Given a string, resolve it to a class definition. The
        various resolver methods may be slow, so the results of this
        function get memoized.
        '''
        if isinstance(ref, types.ClassType):
            return ref
        return self.nodespace.resolve(ref)

    def resolve(self, itemstream):
        '''Try to resolve the incoming stream against the functions
        defined on the class instance.
        '''
        for dispatcher, dispatch_data in self._dispatch_data.items():
            match = dispatcher.dispatch(itemstream, dispatch_data)
            if match is None:
                continue
            method, matched_items = match
            if method is not None:
                return method(self, *matched_items)

        # No matched functions were found.
        if not itemstream:
            raise StopIteration()

        # Propagate up this node's parent.
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
            # Make child ctx lookups fail over to parent.
            self.ctx.adopt(child.ctx)
            if edge is not None:
                self.edge_map[edge] = child
        return child

    def insert(self, index, child):
        '''Insert a child node a specific index.
        '''
        child.parent = self
        self.ctx.adopt(child.ctx)
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
            new_node.ctx = self.ctx
            new_node.local_ctx = self.local_ctx

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

    def first_token(self):
        return self.items[0][1]

    def first_text(self):
        if self.items:
            return self.items[0][2]
        else:
            # XXX: such crap
            return ''

    def pprint(self, offset=0):
        print offset * ' ', '-', self
        for child in self.children:
            child.pprint(offset + 2)

    def pformat(self, offset=0, buf=None):
        buf = buf or []
        buf.extend([offset * ' ', ' - ', repr(self), '\n'])
        for child in self.children:
            child.pformat(offset + 2, buf)
        return ''.join(buf)

    @CachedAttr
    def ctx(self):
        '''For values that are accessible to children
        and inherit from parents.
        '''
        try:
            return self._ctx
        except AttributeError:
            pass

        if hasattr(self, 'parent'):
            ctx = self.parent.ctx.new_child()
        else:
            ctx = ChainMap()
        self._ctx = ctx
        return ctx

    @property
    def local_ctx(self):
        '''For values that won't be accessible to
        chidlren and don't inhreit from parents.
        '''
        try:
            return self._local_ctx
        except AttributeError:
            pass
        _local_ctx = {}
        self._local_ctx = _local_ctx
        return _local_ctx

    @property
    def uuid(self):
        if 'uuid' in self.local_ctx:
            return self.local_ctx['uuid']
        _id = str(uuid.uuid4())
        self.local_ctx['uuid'] = _id
        return _id

    def _depth_first(self):
        yield self
        for child in self.children:
            for node in child._depth_first():
                yield node

    #------------------------------------------------------------------------
    # Querying methods.
    #------------------------------------------------------------------------
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

    def ancestors(self):
        this = self
        while True:
            try:
                parent = this.parent
            except AttributeError:
                return
            else:
                yield parent
            this = parent

    def find(self, type_or_name):
        if isinstance(type_or_name, basestring):
            for node in self._depth_first():
                if node.__class__.__name__ == type_or_name:
                    yield node
        else:
            for node in self._depth_first():
                if isinstance(node, type_or_name):
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
            children=[child.as_data() for child in self.children],
            ctx=self.ctx.map,
            local_ctx=self.local_ctx)

    @classmethod
    def fromdata(cls, data, namespace=None):
        '''
        namespace: is a dict containing all the required
        ast nodes to reconstitute this object.

        json_data: is the nested dict structure.
        '''
        if namespace is None:
            class NameSpace(dict):
                def __missing__(self, cls_name):
                    cls = type(str(cls_name), (Node,), {})
                    self[cls_name] = cls
                    return cls
            namespace = NameSpace()

        node_cls = namespace[data['type']]
        items = []
        for pos, token, text in data['items']:
            items.append((pos, Token.fromstring(token), text))
        node = node_cls(*items)
        children = []
        for child in data['children']:
            child = cls.fromdata(child, namespace)
            child.parent = node
            children.append(child)
        node.children = children
        if 'ctx' in data:
            node.ctx.update(data['ctx'])
        if 'local_ctx' in data:
            node._local_ctx = data['local_ctx']
        return node

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False

        # Don't care if the items are a list or tuple.
        if tuple(self.items) != tuple(other.items):
            return False

        if self.children != other.children:
            return False

        if self.ctx != other.ctx:
            return False

        return True


