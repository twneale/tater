from __future__ import print_function

import re
import uuid
import inspect
import operator
from abc import ABCMeta
from collections import defaultdict, MutableMapping

from tater.core.tokentype import Token

from tater.utils import (
        CachedAttr, CachedClassAttribute, NoClobberDict,
        KeyClobberError, memoize_methodcalls, LoopInterface,
        iterdict_filter, DictFilterMixin)
from tater.utils.chainmap import ChainMap
from tater.utils.itemstream import ItemStream

from tater.base.node.nodespace import NodeSpace
from tater.base.node.resolvers import (
    MetaclassRegistryResolver, LazyImportResolver, LazyTypeCreator)
from tater.base.node.exceptions import ConfigurationError, ParseError


class NodeList(list, DictFilterMixin):
    '''A list subclass that exposes a LoopInterface when
    invoked as a context manager, and can also be iterated
    over in sorted order, given a dict key.

    with node.children.sorted_by('rank') as loop:
        for thing in loop.filter(disqualified=False):
            if loop.first:
                print thing, 'is first!'
            else:
                print thing, 'is the %dth loser' % loop.counter
    '''
    def __enter__(self):
        return LoopInterface(self)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def order_by(self, key):
        '''Sort kids by the specified dictionary key.
        '''
        return self.__class__(sorted(self, key=operator.itemgetter(key)))


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


class BaseNode(dict):
    '''A basic directed graph node optimized for mutability and
    contextual analysis.

    This node class differs from Networkx nodes, which are essentially
    a dictionary-based abstraction optimized for O(1) node lookup.
    '''
    __metaclass__ = _NodeMeta

    # The groups of resolvers attempted (in order) for resolving
    # stringy node references.
    noderef_resolvers = (
        MetaclassRegistryResolver,
        LazyImportResolver,
        LazyTypeCreator)

    @CachedAttr
    def children(self):
        return NodeList()

    # -----------------------------------------------------------------------
    # Custom __eq__ behavior.
    # -----------------------------------------------------------------------
    eq_attrs = ('children',)

    @CachedClassAttribute
    def _eq_attrgetters(self):
        '''Functions that quickly get the attrs marked for
        consideration in determining equality on the class.
        '''
        return map(operator.attrgetter, self.eq_attrs)

    def __eq__(self, other):
        '''Defers to dict.__eq__, then compares attrs specified
        by subclasses.
        '''
        if not super(BaseNode, self).__eq__(other):
            return False
        for getter in self._eq_attrgetters:
            if not getter(self) == getter(other):
                return False
        return True

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, dict.__repr__(self))

    # -----------------------------------------------------------------------
    # Methods related to instance state.
    # -----------------------------------------------------------------------
    @CachedAttr
    def ctx(self):
        '''For values that are accessible to children
        and inherit from parents.

        Construction is lazy to avoid creating a chainmap
        for every node where it's an unused feature.

        Should be used primarily for contextually specific ephemera
        needed for graph traversal, rendering, and mutation.

        Doesn't get serialized.
        '''
        return ChainMap(inst=self)

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

    # -----------------------------------------------------------------------
    # Low-level mutation methods. String references to types not allowed.
    # -----------------------------------------------------------------------
    def append(self, child, related=True):
        '''Related is false when you don't want the child to become
        part of the resulting data structure, as in the case of the
        start node.
        '''
        if related:
            child.parent = self
            self.children.append(child)
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
    def ascend(self, cls_or_name=None, related=True, *args, **kwargs):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        parent = cls_or_name(*args, **kwargs)
        parent.append(self, related)
        return parent

    def descend(self, cls_or_name=None, *args, **kwargs):
        '''Create a new node, set it as a child of this node and return it.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        child = cls(*args, **kwargs)
        return self.append(child)

    def descend_path(self, *cls_or_name_seq):
        '''Descend along the specifed path.
        '''
        this = self
        for cls_or_name in cls_or_name_seq:
            this = this.descend(cls_or_name)
        return this

    def swap(self, cls_or_name=None, *args, **kwargs):
        '''Swap cls(*args, **kwargs) for this node and make this node
        it's child.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        new_parent = self.parent.descend(cls, *args, **kwargs)
        self.parent.remove(self)
        new_parent.append(self)
        return new_parent

    # -----------------------------------------------------------------------
    # Readability functions.
    # -----------------------------------------------------------------------
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

    def depth_first(self):
        yield self
        for child in self.children:
            for node in child.depth_first():
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

    def get_nodekey(self):
        '''This method enables subclasses to customize the
        behavior of ``find`` and ``find_one``. The default
        implementation uses the name of the class.
        '''
        return self.__class__.__name__

    @iterdict_filter
    def find(self, nodekey=None):
        '''Nodekey must be a string.
        '''
        for node in self.depth_first():
            if nodekey is not None:
                if node.get_nodekey() == nodekey:
                    yield node
                else:
                    continue
            else:
                yield node

    def find_one(self, nodekey):
        '''Find the only child matching the criteria.
        '''
        for node in self.find(nodekey):
            return node

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    def _children_to_data(children):
        return [kid.to_data() for kid in children]

    _serialization_meta = (
        dict(attr='__class__.__name__', alias='type'),
        dict(
            attr='children',
            to_data=_children_to_data),
        )

    def to_data(self):
        '''Render out this object as a json-serializable dictionary.
        '''
        data = dict(data=dict(self))
        for meta in self._serialization_meta:
            attr = meta['attr']
            alias = meta.get('alias', attr)
            to_data = meta.get('to_data')
            value = operator.attrgetter(attr)(self)
            if to_data is not None:
                value = to_data(value)
            data[alias] = value
        return data

    @classmethod
    def fromdata(cls, data, default_node_cls=None):
        '''
        '''
        # Create a new node.
        nodespace = cls.nodespace

        # Figure out what node_cls to use.
        if default_node_cls is None:
            type_ = data.get('type')
            if type_ is not None:
                node_cls = nodespace.resolve(str(type_))
            else:
                node_cls = cls
        else:
            node_cls = default_node_cls

        node = node_cls(data['data'])

        # Add the children.
        children = []
        for child in data['children']:
            child = cls.fromdata(child)
            node.append(child)

        # Add any other attrs marked for inclusion by the class def.
        for meta in cls._serialization_meta:
            meta = dict(meta)
            if meta.get('alias') == 'type':
                continue
            if meta['attr'] == 'children':
                continue
            fromdata = meta.get('fromdata')

            attr = meta['attr']
            alias = meta.get('alias', attr)
            val = data[alias]
            if fromdata is not None:
                val = fromdata(val)
            object.__setattr__(node, attr, val)

        # Postdeserialize hook, just in case.
        post_deserialize = getattr(node_cls, 'post_deserialize', None)
        if post_deserialize is not None:
            post_deserialize(node)

        return node

    #------------------------------------------------------------------------
    # Random utils.
    #------------------------------------------------------------------------
    @CachedAttr
    def uuid(self):
        '''Just a convenience for quickly generating uuid4's. The built-in
        ``id`` function is probably more idiomatic for most purposes.
        '''
        return str(uuid.uuid4())


class BaseSyntaxNode(BaseNode):

    eq_attrs = ('children', 'tokens', '__class__.__name__',)

    @CachedAttr
    def tokens(self):
        return []

    #------------------------------------------------------------------------
    # Parsing and dispatch methods.
    #------------------------------------------------------------------------
    def popstate(self):
        '''Just for readability and clarity about what it means
        to return the parent.'''
        return self.parent

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
    # Readability functions.
    # -----------------------------------------------------------------------
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

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    @staticmethod
    def _tokens_as_data(self, tokens):
        _tokens = []
        for (pos, token, text) in tokens:
            _tokens.append((pos, token.as_json(), text))
        return tokens

    def _tokens_from_data(self, tokens):
        _tokens = []
        for pos, token, text in tokens:
            _tokens.append((pos, Token.fromstring(token), text))
        return _tokens

    as_data_attrs = (
        dict(attr='__class__.__name__', alias='type'),
        dict(attr='children'),
        dict(
            attr='tokens',
            to_data=_tokens_as_data,
            fromdata=_tokens_from_data),
        )

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
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


def new_basenode(*bases):
    '''Create a new base node type with its own distinct nodespace.
    This provides a way to reuse node names without name conflicts in the
    metaclass cache.
    '''
    return type('Node', bases, dict(nodespace=NodeSpace()))


Node = new_basenode(BaseNode)
SyntaxNode = new_basenode(BaseSyntaxNode)


