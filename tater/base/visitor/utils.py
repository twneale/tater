
class MethodDict(dict):
    'Dict for caching visitor methods.'
    def __init__(self, visitor):
        self.visitor = visitor
        self.get_nodekey = visitor.get_nodekey

    def __missing__(self, node):
        name = self.get_nodekey(node)
        method = getattr(self.visitor, 'visit_' + name, None)
        self[name] = method
        return method
