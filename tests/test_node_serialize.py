from unittest import TestCase

from nose.tools import assert_equals, set_trace
from tater import Node, Token as t


class TestNodeSerialize(TestCase):

    def test_as_json(self):

        class MyNode(Node):
            '''Test node.
            '''
        items = [
            (0, t.Test1, 'cow'),
            (3, t.Test2, 'pig'),
            (6, t.Test3, 'donkey'),
            ]

        # Create a node and add some kids.
        node = MyNode(*items)
        child = node.descend(MyNode, items)
        child = child.descend(MyNode, items)
        namespace = dict(MyNode=MyNode)

        expected = node
        as_data = node.as_data()
        found = Node.fromdata(as_data, namespace)
        assert_equals(expected, found)
