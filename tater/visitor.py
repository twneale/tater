'''
Note: it's critical to visit a copy of node.children,
otherwise children might be mutated by the visitor
functions, causing the visitor to skip children
and not visit them.
'''
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
    class Continue(Exception):
        '''If a user-defined visitor function raises this exception,
        children of the visited node won't be visited.
        '''

    @CachedAttr
    def _methods(self):
        return _MethodDict(visitor=self)

    def visit(self, node):
        self.node = node
        self.visit_nodes(node)
        return self.finalize()

    def visit_nodes(self, node):
        try:
            self.visit_node(node)
        except self.Continue:
            # Skip visiting the child nodes.
            return
        visit_nodes = self.visit_nodes
        for child in node.children[:]:
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
        '''Final steps the visitor needs to take, plus the
        return value or .visit, if any.
        '''
        return self


class Transformer(Visitor):
    '''A visitor that replaces the visited node with the
    output of the visitor function.
    '''
    def visit_nodes(self, node):
        '''If the visitor function returns a new node, replace
        the current node with it, then stop.

        Otherwise, continue on down the tree.
        '''
        try:
            new_node = self.visit_node(node)
        except self.Continue:
            # Skip visiting the child nodes.
            return
        if new_node is not None:
            node.replace(new_node)
            return
        visit_nodes = self.visit_nodes
        for child in node.children[:]:
            visit_nodes(child)


class Renderer(Visitor):
    '''The visitor functions on this visitor are context manages.
    They perform some action initially, then delegate to the node's
    child functions all the way down the tree, then perform a final,
    closing action, like closing at html tag.

    from contextlib import contextmanager
    from StringIO import StringIO

    form tater.visitor import Renderer


    class MyRenderer(Render):

        def __init__(self):
            self.buf = StringIO()

        @contextmanager
        def visit_div(self, node):
            self.buf.write('<div>')
            self.buf.write(node.first_text())
            yield
            self.buf.write('</div>')
    '''
    def visit_nodes(self, node):
        '''If the visitor function is a context manager, invoke it,
        otherwise just run the function.
        '''
        func = self._methods[node]

        # If no function is defined, run the generic visit function.
        if func is None:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is None:
                return
            return generic_visit(node)

        # Test if the function is a context manager. If so, invoke it.
        else:
            try:
                with func(node):
                    visit_nodes = self.visit_nodes
                    for child in node.children[:]:
                        visit_nodes(child)
            except self.Continue:
                    pass


class _Orderer(Visitor):

    def __init__(self):
        self.nodes = []

    def visit_node(self, node):
        self.nodes.append(node)

    def _sortfunc(self, node):
        if node.items:
            for pos, token, text in node.items:
                return pos

    def finalize(self):
        return sorted(self.nodes, key=self._sortfunc)


class OrderedRenderer(Visitor):
    '''In sort nodes, method, chooses the order in which
    to visit children based on their index vals. Probz doesn't
    need a helper class to do that. ACTUALLY YES IT DOES.
    '''
    def visit(self, node):
        self.ordered = _Orderer().visit(node)
        super(OrderedRenderer, self).visit(node)

    def visit_nodes(self, node):
        '''If the visitor function is a context manager, invoke it,
        otherwise just run the function.
        '''
        func = self._methods[node]

        # If no function is defined, run the generic visit function.
        if func is None:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is None:
                return
            return generic_visit(node)

        # Test if the function is a context manager. If so, invoke it.
        else:
            with func(node):
                visit_nodes = self.visit_nodes
                for child in node.children[:]:  # sorted(node.children, key=self.ordered.index):
                    visit_nodes(child)
