import networkx as nx

from tater import Node, Visitor


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
                G.add_node(node_id, **node)

    def generic_visit(self, node):
        parent = getattr(node, 'parent', None)
        if parent is None:
            return
        self.maybe_add_nodes(node, parent)
        parent_id = self.get_node_id(parent)
        node_id = self.get_node_id(node)
        self.G.add_edge(parent_id, node_id)

    def finalize(self):
        return self.G


def to_digraph(root):
    return DiGraphRenderer().visit(root)


class DiGraphLoader(object):

    def __init__(self, G, root_id):
        self.G = G
        self.root = Node(G.node[root_id])
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
        node = Node(**node)
        self.seen[node_id] = node

    def add_edge(self, src, dest):
        src = self.seen[src]
        dest = self.seen[dest]
        src.append(dest)


def from_digraph(G, root_id):
    return DiGraphLoader(G, root_id).build()
