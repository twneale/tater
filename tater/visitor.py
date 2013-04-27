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
    '''Define a generic_visit function to do the same
    thing on each node.
    '''
    @CachedAttr
    def _methods(self):
        return _MethodDict(visitor=self)

    def visit(self, node):
        self.node = node
        self.visit_nodes(node)
        self.finalize()
        return self

    def visit_nodes(self, node):
        self.visit_node(node)
        visit_nodes = self.visit_nodes
        for child in node.children:
            visit_nodes(child)

    def visit_node(self, node):
        func = self._methods[node]
        if func is not None:
            return func(node)
        else:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is not None:
                return generic_visit(node)

    def finalize(self):
        pass


class Transformer(Visitor):
    '''A visitor that replaces the visited node with the
    output of the visitor function.
    '''
    def visit_nodes(self, node):
        '''If the visitor function returns a new node, replace
        the current node with it, then stop.

        Otherwise, continue on down the tree.
        '''
        new_node = self.visit_node(node)
        if new_node is not None:
            node.replace(new_node)
            return
        visit_nodes = self.visit_nodes
        for child in node.children:
            visit_nodes(child)
