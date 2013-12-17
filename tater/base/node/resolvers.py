import sys

from tater.utils import CachedAttr
from tater.core import logger
from tater.base.node.exceptions import AmbiguousNodeNameError


class NodeResolver(object):
    '''Each resolver class has a resolve method that will try
    to resolve a string name to an actual node class.
    '''
    __slots__ = ('nodespace',)

    def __init__(self, nodespace):
        self.nodespace = nodespace

    def resolve(self, name):
        raise NotImplementedError()


class AnonymousNodesModule(object):
    pass


class MetaclassRegistryResolver(NodeResolver):
    '''This resolver tries to resolve string references like 'MyNode'
    to a keyed type in the metaclass cache.
    '''
    def resolve(self, name):
        nodes = self.nodespace.registry.get(name)
        if not nodes:
            return
        if 1 < len(nodes):
            msg = 'There are %d registered node types named %r'
            raise AmbiguousNodeNameError(msg % (len(nodes), name))
        return nodes.pop()


class LazyImportResolver(NodeResolver):
    '''This resolver tries to import type reference strings
    like 'mypackage.mymodule.MyClass'. The idea is provide functionality
    similar to django's url patterns and celery's task names.
    '''
    def resolve(self, name):
        module_name, _, name = name.rpartition('.')
        try:
            module = __import__(module_name, globals(), locals(), [name], -1)
        except ImportError:
            return
        try:
            return getattr(module, name)
        except:
            return


class LazyTypeCreator(NodeResolver):
    '''This resolver creates missing types (but warns when it does).
    '''
    module = AnonymousNodesModule()
    sys.modules['tater_anonymous_nodes'] = module

    @CachedAttr
    def Node(self):
        '''Circular import avoidance hack.
        '''
        from tater.base.node import Node
        return Node

    @CachedAttr
    def module(self):
        return sys.modules[self.Node.__class__.__module__]

    def resolve(self, name):
        logger.debug('Automatically creating undefined class %r.' % name)
        cls = type(name, (self.Node,), {})
        setattr(self.module, name, cls)
        return cls