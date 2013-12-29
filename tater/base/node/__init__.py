import re
import uuid
import inspect
from abc import ABCMeta
from collections import defaultdict, MutableMapping

from tater.core.tokentype import Token

from tater.utils import (
        CachedAttr, CachedClassAttribute, NoClobberDict,
        KeyClobberError, memoize_methodcalls)
from tater.utils.chainmap import ChainMap
from tater.utils.itemstream import ItemStream

from tater.base.node.nodespace import NodeSpace
from tater.base.node.resolvers import (
    MetaclassRegistryResolver, LazyImportResolver, LazyTypeCreator)
from tater.base.node.exceptions import ConfigurationError, ParseError


class _NodeMeta(ABCMeta):

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


class BaseNode(dict):
    '''
    '''
    __metaclass__ = _NodeMeta

    noderef_resolvers = (
        MetaclassRegistryResolver,
        LazyImportResolver,
        LazyTypeCreator)

    @CachedAttr
    def tokens(self):
        return []

    @CachedAttr
    def children(self):
        return []

    def popitem(self):
        return self.local_ctx.popitem(key)

    # -----------------------------------------------------------------------
    # Other custom behavior.
    # -----------------------------------------------------------------------
    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return False

        # Don't care if the tokens are a list or tuple.
        if tuple(self.tokens) != tuple(other.tokens):
            return False

        if self.children != other.children:
            return False

        if self.local_ctx != other.local_ctx:
            return False

        return True

    def __hash__(self):
        '''This is pretty bad. These objects are mutable and shouldn't be
        hashable.
        '''
        return hash(self.uuid)

    # -----------------------------------------------------------------------
    # Methods related to instance state.
    # -----------------------------------------------------------------------
    @CachedAttr
    def ctx(self):
        '''For values that are accessible to children
        and inherit from parents.

        Construction is lazy to avoid creating a chainmap
        for every node where it's an unused feature.
        '''
        return ChainMap(inst=self)

    @CachedAttr
    def local_ctx(self):
        '''For values that won't be accessible to
        chidlren and don't inhreit from parents.
        '''
        return {}

    @CachedAttr
    def uuid(self):
        return str(uuid.uuid4())

    # -----------------------------------------------------------------------
    # Dispatch and parsing methods.
    # -----------------------------------------------------------------------
    @memoize_methodcalls
    def resolve_noderef(self, ref):
        '''Given a string, resolve it to a class definition. The
        various resolver methods may be slow, so the results of this
        function get memoized.
        '''
        if isinstance(ref, basestring):
            return self.nodespace.resolve(ref)
        return ref

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

        # Itemstream is exhausted.
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

    @classmethod
    def parse(cls_or_inst, itemiter, **options):
        '''Supply a user-defined start class.
        '''
        itemstream = ItemStream(itemiter)

        if callable(cls_or_inst):
            node = cls_or_inst()
        else:
            node = cls_or_inst

        while 1:
            try:
                if options.get('debug'):
                    print '%r <-- %r' % (node, itemstream)
                    node.getroot().pprint()
                node = node.resolve(itemstream)
            except StopIteration:
                break
        return node.getroot()

    # -----------------------------------------------------------------------
    # Low-level mutation methods. String references to types not allowed.
    # -----------------------------------------------------------------------
    def append(self, child, related=True, edge=None):
        '''Related is false when you don't want the child to become
        part of the resulting data structure, as in the case of the
        start node.
        '''
        if related:
            child.parent = self
            self.children.append(child)
            # Make child ctx lookups fail over to parent.
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

    def detatch(self):
        '''Remove this node from parent.
        '''
        self.parent.remove(self)
        return self

    def remove(self, child):
        'Um, should this return something? Not sure.'
        self.children.remove(child)

    # -----------------------------------------------------------------------
    # High-level mutation methods. String references to types allowed.
    # -----------------------------------------------------------------------
    def ascend(self, cls_or_name, items=None, related=True):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        cls = self.resolve_noderef(cls_or_name)
        items = items or []
        parent = cls_or_name(*items)
        parent.append(self, related)
        return parent

    def descend(self, cls_or_name, items=None):
        cls = self.resolve_noderef(cls_or_name)
        items = items or []

        # Put single item into a list. This sucks.
        if items and isinstance(items[0], int):
            items = [items]

        child = cls(*items)
        return self.append(child)

    def descend_many(self, *cls_or_name_seq):
        this = self
        for cls_or_name in cls_or_name_seq:
            cls = self.resolve_noderef(cls_or_name)
            child = cls()
            this = this.append(child)
        return this

    def swap(self, cls_or_name, items=None):
        '''Swap cls(*items) for this node and make this node
        it's child.
        '''
        cls = self.resolve_noderef(cls_or_name)
        items = items or []
        new_parent = self.parent.descend(cls, items)
        self.parent.remove(self)
        new_parent.append(self)
        return new_parent

    def replace(self, cls_or_node_or_name, items=None, transfer=False):
        '''Replace this node wholesale with the specified child.
        Preserve order.
        '''
        if isinstance(cls_or_node_or_name, basestring):
            cls = self.resolve_noderef(cls_or_node_or_name)
        items = items or []
        parent = self.parent
        children = parent.children
        index = children.index(self)

        # Remove this node.
        children.remove(self)

        if isinstance(cls_or_node_or_name, Node):
            # If a node was passed in, insert it.
            new_node = cls_or_node_or_name
        else:
            # Otherwise create a new node.
            cls = cls_or_node_or_name
            new_node = cls(*items)
            new_node.ctx = self.ctx
            new_node.local_ctx = self.local_ctx

        if transfer:
            new_node.children.extend(self.children)

        return parent.insert(index, new_node)

    # -----------------------------------------------------------------------
    # Readability functions.
    # -----------------------------------------------------------------------
    def popstate(self):
        '''Just for readability and clarity about what it means
        to return the parent.'''
        return self.parent

    def extend(self, *items):
        self.tokens.extend(items)
        return self

    def first(self):
        return self.tokens[0]

    def first_token(self):
        return self.tokens[0].token

    def first_text(self):
        if self.tokens:
            return self.tokens[0].text
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

    #------------------------------------------------------------------------
    # Querying methods.
    #------------------------------------------------------------------------
    def getroot(self):
        this = self
        while hasattr(this, 'parent'):
            this = this.parent
        return this

    def _depth_first(self):
        yield self
        for child in self.children:
            for node in child._depth_first():
                yield node

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

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    def as_data(self):
        items = []
        for (pos, token, text) in self.tokens:
            items.append((pos, token.as_json(), text))
        return dict(
            type=self.__class__.__name__,
            tokens=items,
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
                    # This can probably be replaced by recent code to gerenate
                    # ananymous types.
                    cls = type(str(cls_name), (Node,), {})
                    self[cls_name] = cls
                    return cls
            namespace = NameSpace()

        node_cls = namespace[data['type']]
        items = []
        for pos, token, text in data['tokens']:
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


def new_basenode():
    '''Create a new base node type with its own distinct nodespace.
    This provides a way to reuse node names without name conflicts in the
    metaclass cache.
    '''
    return type('Node', (BaseNode,), dict(nodespace=NodeSpace()))


Node = new_basenode()


