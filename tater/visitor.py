from tater.utils import CachedAttr


class _MethodDict(dict):
    'Dict for caching visitor methods.'
    def __init__(self, visitor):
        self.visitor = visitor

    def __missing__(self, node):
        name = node.__class__.__name__
        method = getattr(self.visitor, 'visit_' + name, None)
        self[name] = method
        return method


class Visitor(object):

    @CachedAttr
    def _methods(self):
        return _MethodDict(visitor=self)

    def visit(self, node):
        self.node = node
        self.visit_nodes(node)
        self.finalize()

    def visit_nodes(self, node):
        self.visit_node(node)
        visit_nodes = self._visit_nodes
        for child in node.children:
            visit_nodes(child)

    def visit_node(self, node):
        func = self._methods.get(node, self.generic_visit)
        if func is not None:
            return func(node)

    def generic_visit(self, node):
        pass

    def finalize(self):
        pass
