from unittest import TestCase
from nose.tools import assert_equals

from tater import Node


class TestLazyImportResolver(TestCase):

    def test_lazy_import(self):
        deref = Node().resolve_noderef('tater.base.node.Node')
        assert_equals(deref, Node)
