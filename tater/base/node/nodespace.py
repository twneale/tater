from collections import defaultdict


class NodeSpace(object):
    '''A namespace for node types.
    '''
    __slots__ = ('registry', 'resolvers')

    def __init__(self):
        self.resolvers = []
        self.registry = defaultdict(list)

    def register(self, cls):
        self.registry[cls.__name__].append(cls)

    def add_resolvers(self, *resolvers):
        for resolver in resolvers:
            self.resolvers.append(resolver(self).resolve)

    def resolve(self, name):
        for resolver in self.resolvers:
            node = resolver(name)
            if node is not None:
                return node

