'''Tools for visiting html and xml etrees, and for converting tater graphs
 to and from etrees.
'''
import re
import functools

import lxml.etree as et
from lxml.html import HtmlComment

from tater import Visitor, Node


class XmlEtreeVisitor(Visitor):

    def visit(self, el):
        self.el = el
        self.visit_nodes(el)
        return self.finalize()

    def get_children(self, el):
        return tuple(el)

    def get_nodekey(self, el):
        return el.tag


class HtmlEtreeVisitor(XmlEtreeVisitor):

    def visit_HtmlComment(self, node):
        '''Skip comments.
        '''
        raise self.Continue()


class _TaterXmlEtreeConverter(Visitor):

    def get_nodekey(self, node):
        return node['tag']

    def finalize(self):
        return et.tostring(self.root)

    def generic_visit(self, node):
        root = getattr(self, 'root', None)
        if root is None:
            attrs = dict(node)
            tag = attrs.pop('tag')
            root = et.Element(tag, **attrs)
            self.root = root
        else:
            attrs = dict(node)
            tag = attrs.pop('tag')
            et.SubElement(root, tag, **attrs)


def to_etree(node):
    return _TaterXmlEtreeConverter().visit(node)


def from_etree(
    el, node=None, node_cls=None,
    tagsub=functools.partial(re.sub, r'\{.+?\}', ''),
    Node=Node):
    '''Convert the element tree to a tater tree.
    '''
    node_cls = node_cls or Node
    node = node or node_cls()
    tag = tagsub(el.tag)
    attrib = dict((tagsub(k), v) for (k, v) in el.attrib.items())
    node.update(attrib, tag=tag)

    if el.text:
        node['text'] = el.text
    for child in el:
        child = from_etree(child, node_cls=node_cls)
        node.append(child)
    if el.tail:
        node['tail'] = el.tail
    return node


def from_html(
    el, node=None, node_cls=None,
    tagsub=functools.partial(re.sub, r'\{.+?\}', ''),
    Node=Node, HtmlComment=HtmlComment):
    '''Convert the element tree to a tater tree.
    '''
    node_cls = node_cls or Node
    node = node or node_cls()
    tag = tagsub(el.tag)
    attrib = dict((tagsub(k), v) for (k, v) in el.attrib.items())
    node.update(attrib, tag=tag)

    if el.text:
        node['text'] = el.text
    for child in el:
        if isinstance(child, HtmlComment):
            continue
        elif getattr(child, '__name__', None) == 'Comment':
            continue
        child = from_html(child, node_cls=node_cls)
        node.append(child)
    if el.tail:
        node['tail'] = el.tail
    return node


