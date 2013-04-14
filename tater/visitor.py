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
        self._visit_nodes(node)
        self.finalize()

    def _visit_nodes(self, node):
        self._visit_node(node)
        visit_nodes = self._visit_nodes
        for child in node.children:
            visit_nodes(child)

    def _visit_node(self, node):
        func = self._methods[node]
        if func is not None:
            return func(node)

    def finalize(self):
        pass
