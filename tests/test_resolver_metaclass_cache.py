from unittest import TestCase
from nose.tools import assert_equals, assert_raises

from tater import Node
from tater.base.node.exceptions import AmbiguousNodeNameError


class TestMetaclassCacheResolver(TestCase):

    def test_sequence(self):
        '''Make sure metaclass class resolution works.
        '''
        deref = Node().resolve_noderef('TestNode')
        assert_equals(TestNode, deref)


    def test_dupenode(self):
        node = Node()
        assert_raises(AmbiguousNodeNameError, node.resolve_noderef, 'DupeNode')


class TestNode(Node):
    pass


class DupeNode(Node):
    pass


class Dummy:

    class DupeNode(Node):
        '''This should cause a name conflict.
        '''