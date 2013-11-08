from unittest import TestCase

from tater import Node
from tater import tokenseq

from nose.tools import assert_equals, set_trace


class Node1(Node):
    @tokenseq('A', 'B', 'C')
    def handle_abc(self, *items):
        return self.descend('Node2', items)

class Node2(Node):
    @tokenseq('D', 'E')
    def handle_de(self, *items):
        return self.descend(Node2, items)


class TestTokentypeSequence(TestCase):

    items = [
        (1, 2, 'A'), (2, 3, 'B'), (3, 4, 'C'),
        (3, 4, 'D'), (3, 4, 'E')]
    def test_sequence(self):
        x = Node1.parse(self.items)
