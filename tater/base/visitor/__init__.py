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

    def apply_visitor_method(self, method_data, node):
        if hasattr(method_data, '__call__'):
            return method_data(node)
        elif isinstance(method_data, tuple):
            method = method_data[0]
            args = method_data[1:]
            return method(*args)

    def visit_node(self, node, gentype=contextlib.GeneratorContextManager):
        '''Given a node, find the matching visitor function (if any) and
        run it. If the result is a context manager, yield from all the nodes
        children before allowing it to exit. Otherwise, return the result.
        '''
        method_data = self.get_method(node)

        if method_data is not None:
            # If it's a context manager, enter, visit children, then exit.
            # Otherwise just return the result.

            result = self.apply_visitor_method(method_data, node)
            if isinstance(result, gentype):
                with result:
                    visit_nodes = self.visit_nodes
                    for child in self.get_children(node):
                        try:
                            visit_nodes(child)
                        except self.Continue:
                            continue
            else:
                return result
        else:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is not None:
                return generic_visit(node)

    def get_nodekey(self, node):
        '''Given a node, return the string to use in computing the
        matching visitor methodname. Can also be a generator of strings.
        '''
        yield node.__class__.__name__

    def get_children(self, node):
        '''Given a node, return its children.
        '''
        return node.children[:]

    def get_methodnames(self, node):
        '''Given a node, generate all names for matching visitor methods.
        '''
        key_or_iter = self.get_nodekey(node)
        if isinstance(key_or_iter, basestring):
            yield 'visit_' + key_or_iter
        for key in key_or_iter:
            yield 'visit_' + key

    def get_method(self, node):
        '''Given a particular node, check the visitor instance for methods
        mathing the computed methodnames (the function is a generator).
        '''
        methods = self.methods
        for methodname in self.get_methodnames(node):
            if methodname in methods:
                return methods[methodname]
            else:
                method = getattr(self, methodname, None)
                if method is not None:
                    methods[methodname] = method
                    return method

    def finalize(self):
        '''Final steps the visitor needs to take, plus the
        return value of .visit, if any.
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
            for token in self.itervisit_node(node):
                yield token
        except self.Continue:
            # Skip visiting the child nodes.
            return
        visit_nodes = self.itervisit_nodes
        for child in self.get_children(node):
            for result in visit_nodes(child):
                yield result

    def itervisit_node(
            self, node, gentype=types.GeneratorType,
            ctx_gentype=contextlib.GeneratorContextManager):
        '''Given a node, find the matching visitor function (if any) and
        run it. If the result is a context manager, yield from all the nodes
        children before allowing it to exit. Otherwise, return the result.
        '''
        func = self.get_method(node)
        if func is not None:

            # If it's a generator, yield the results.
            result = func(node)
            if isinstance(result, gentype):
                for token in result:
                    yield token

            # If it's a context manager, enter, visit children, then exit.
            # Otherwise just return the result.
            elif isinstance(result, ctx_gentype):
                with result:
                    visit_nodes = self.visit_nodes
                    for child in self.get_children(node):
                        try:
                            for token in visit_nodes(child):
                                yield token
                        except self.Continue:
                            continue
            else:
                yield result
        else:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is not None:
                for token in generic_visit(node):
                    yield token


    def get_children(self, node):
        '''Override this to determine how child nodes are accessed.
        '''
        return node.children[:]

