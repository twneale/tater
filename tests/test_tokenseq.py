from unittest import TestCase

from tater import Node, parse
from tater import Token as t
from tater import tokenseq

from nose.tools import assert_equals, set_trace


class Node1(Node):
    @tokenseq(t.A, t.B, t.C)
    def handle_abc(self, *items):
        return self.descend(Node2, items)

class Node2(Node):
    @tokenseq(t.D, t.E)
    def handle_de(self, *items):
        return self.descend(Node2, items)


class TestTokentypeSequence(TestCase):

    items = [(1, 2, t.A), (2, 3, t.B), (3, 4, t.C), (3, 4, t.D), (3, 4, t.E)]
    def test_sequence(self):
        x = parse(Node1, self.items)
