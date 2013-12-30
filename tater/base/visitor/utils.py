
class MethodCache(dict):
    'Dict for caching visitor methods.'
    def __init__(self, visitor):
        self.visitor = visitor
        self.cache = {}
        self.get_nodekey = visitor.get_nodekey

    def check(self, node):
        name = self.get_nodekey(node)
        method = self.cache.get(name)
        if method is not None:
            return method
        method = getattr(self.visitor, 'visit_' + name, None)
        self.cache[name] = method
        return method

    def __missing__(self, node):
        self[name] = method
        return method
