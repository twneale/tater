import networkx as nx

from tater import Node, Visitor, IteratorVisitor


class DiGraphVisitor(Visitor):

    def __init__(self, G):
        self.G = G

    def get_children(self, node):
        return self.G.successors(node)

    def finalize(self):
        '''Final steps the visitor needs to take, plus the
        return value or .visit, if any.
        '''
        return self


class DiGraphIteratorVisitor(IteratorVisitor):

    def __init__(self, G):
        self.G = G

    def get_children(self, node):
        return self.G[node]

    def finalize(self):
        '''Final steps the visitor needs to take, plus the
        return value or .visit, if any.
        '''
        return self


class DiGraphRenderer(Visitor):

    def __init__(self):
        self.G = nx.DiGraph()

    def get_node_id(self, node):
        return node.uuid

    def maybe_add_nodes(self, *nodes):
        G = self.G
        for node in nodes:
            node_id = self.get_node_id(node)
            if node_id not in G.node:
                nx_node = node.to_data()
                del nx_node['children']
                G.add_node(node_id, nx_node)

    def generic_visit(self, node):
        self.maybe_add_nodes(node)
        parent = getattr(node, 'parent', None)
        if parent is None:
            return
        self.maybe_add_nodes(parent)
        parent_id = self.get_node_id(parent)
        node_id = self.get_node_id(node)
        self.G.add_edge(parent_id, node_id)

    def finalize(self):
        return self.G


def to_digraph(root):
    return DiGraphRenderer().visit(root)


class DiGraphLoader(object):

    def __init__(self, G, root_id, node_cls=None):
        self.node_cls = node_cls or Node
        self.G = G
        self.root = self.node_cls(G.node[root_id])
        self.seen = {root_id: self.root}

    def build(self):
        for node in self.G.nodes():
            self.add_node(node)
        for edge in self.G.edges():
            self.add_edge(*edge)
        return self.root

    def add_node(self, node_id):
        if node_id in self.seen:
            return
        node = self.G.node[node_id]
        node = self.node_cls.fromdata(node)
        self.seen[node_id] = node

    def add_edge(self, src, dest):
        src = self.seen[src]
        dest = self.seen[dest]
        src.append(dest)


def from_digraph(G, root_id, node_cls=None):
    return DiGraphLoader(G, root_id, node_cls).build()
