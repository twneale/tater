import types
from contextlib import contextmanager

from tater import Node
from tater.base.visitor import Visitor, IteratorVisitor


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
            if node in node.parent.children:
                node.replace(new_node)
            return
        visit_nodes = self.visit_nodes
        for child in node.children[:]:
            visit_nodes(child)


class Renderer(Visitor):
    '''The visitor functions on this visitor are context managers.
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
        method = self._methods.check(node)

        # If no function is defined, run the generic visit function.
        if method is None:
            generic_visit = getattr(self, 'generic_visit', None)
            if generic_visit is None:
                return
            method = generic_visit

        self._run_visitor_method(method, node)

    def _run_visitor_method(self, method, node):
        if getattr(method, '_is_contextmanager', False):
            with method(node):
                visit_nodes = self.visit_nodes
                for child in self.get_children(node):
                    try:
                        visit_nodes(child)
                    except self.Continue:
                        continue
        else:
            return method(node)


def render(method):
    '''Poorly named thin wrapper for context manager decorator.
    '''
    method = contextmanager(method)
    method._is_contextmanager = True
    return method


class _Orderer(Visitor):

    def __init__(self):
        self.nodes = []

    def visit_node(self, node):
        self.nodes.append(node)

    def _sortfunc(self, node):
        if node.tokens:
            for pos, token, text in node.tokens:
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
        func = self._methods.check(node)

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


class DiGraphVisitor(Visitor):

    def __init__(self, G):
        self.G = G

    def get_children(self, node):
        return self.G[node]

    def finalize(self):
        '''Final steps the visitor needs to take, plus the
        return value or .visit, if any.
        '''
        return self


# ---------------------------------------------------------------------------
# Helpers for figuring out the start/end indexes of a parse tree.
# ---------------------------------------------------------------------------
class IndexVisitor(Visitor):
    '''Base for visitors that aggregate information about
    string indices of modeled text.
    '''
    def __init__(self):
        self.indices = []


class StartIndexVisitor(IndexVisitor):
    '''This visitor finds the starting index of the left-most string
    modeled by the ast.
    '''
    def get_index(self):
        if self.indices:
            return min(self.indices)

    def generic_visit(self, node):
        for pos, token, text in node.tokens:
            self.indices.append(pos)


class EndIndexVisitor(IndexVisitor):
    '''This visitor finds the ending index of the right-most string
    modeled by the ast.
    '''

    def get_index(self):
        if self.indices:
            return max(self.indices)

    def generic_visit(self, node):
        '''The end index will be the `pos` obtained from
        the lexer, plus the length of the associated text.
        '''
        for pos, token, text in node.tokens:
            self.indices.append(pos + len(text))


def get_start(tree):
    return StartIndexVisitor().visit(tree).get_index()


def get_end(tree):
    return EndIndexVisitor().visit(tree).get_index()


def get_span(tree):
    return (get_start(tree), get_end(tree))


# ---------------------------------------------------------------------------
# Helpers for getting leaf nodes.
# ---------------------------------------------------------------------------
class LeafYielder(IteratorVisitor):

    def generic_visit(self, node):
        if not node.children:
            yield node


def get_leaf_nodes(node):
    return LeafYielder().itervisit(node)


# ---------------------------------------------------------------------------
# Stateless stream visitor.
# ---------------------------------------------------------------------------
class StreamVisitor(Visitor):

    def visit(self, iterable, gentype=types.GeneratorType):
        '''The main visit function. Visits the passed-in node and calls
        finalize.
        '''
        self.iterable = iter(iterable)
        for token in self.iterable:
            result = self.visit_node(token)
            if isinstance(result, gentype):
                for output in result:
                    yield output
            elif result is not None:
                yield result
        result = self.finalize()
        if isinstance(result, gentype):
            for output in result:
                yield output

    def get_nodekey(self, token):
        '''Given a particular token, check the visitor instance for methods
        mathing the computed methodnames (the function is a generator).
        '''
        if isinstance(token, basestring):
            yield 'basestring'
        else:
            yield type(token).__name__
            yield token.__class__.__name__
