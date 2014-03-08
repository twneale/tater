'''
Note: it's critical to visit a copy of node.children,
otherwise children might be mutated by the visitor
functions, causing the visitor to skip children
and not visit them.
'''
import types
import contextlib
from tater.utils import CachedAttr


class Visitor(object):
    '''Define a generic_visit function to do the same
    thing on each node.
    '''
    class Continue(Exception):
        '''If a user-defined visitor function raises this exception,
        children of the visited node won't be visited.
        '''

    class Break(Exception):
        '''If raised, the visit is immediately done,
        so stop and call finalize.
        '''

    @CachedAttr
    def methods(self):
        return {}

    def visit(self, node):
        '''The main visit function. Visits the passed-in node and calls
        finalize.
        '''
        self.node = node
        try:
            self.visit_nodes(node)
        except self.Break:
            pass
        return self.finalize()

    def visit_nodes(self, node):
        '''Visit the passed in node and each of its children.
        '''
        try:
            self.visit_node(node)
        except self.Continue:
            # Skip visiting the child nodes.
            return
        visit_nodes = self.visit_nodes
        for child in self.get_children(node):
            visit_nodes(child)

    def visit_node(self, node):
        func = self._methods.check(node)
        if func is not None:
            return func(node)
        else:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is not None:
                return generic_visit(node)

    def get_nodekey(self, node):
        return node.__class__.__name__

    def get_children(self, node):
        return node.children[:]

    def finalize(self):
        '''Final steps the visitor needs to take, plus the
        return value or .visit, if any.
        '''
        return self


class IteratorVisitor(Visitor):

    def itervisit(self, node):
        self.node = node
        for result in self.itervisit_nodes(node):
            if result is not None:
                yield result

    def itervisit_nodes(self, node):
        try:
            yield self.itervisit_node(node)
        except self.Continue:
            # Skip visiting the child nodes.
            return
        visit_nodes = self.itervisit_nodes
        for child in self.get_children(node):
            for result in visit_nodes(child):
                yield result

    def itervisit_node(self, node):
        func = self._methods.get(node)
        if func is not None:
            return func(node)
        else:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is not None:
                return generic_visit(node)

    def get_children(self, node):
        '''Override this to determine how child nodes are accessed.
        '''
        return node.children[:]

