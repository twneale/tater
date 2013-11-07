from unittest import TestCase
from nose.tools import assert_equals, assert_raises

from tater import Node


class TestLazyCreateType(TestCase):

    def test_create(self):
        lazynode = Node().resolve_noderef('LazyNode')
        self.assertTrue(issubclass(lazynode, Node))
