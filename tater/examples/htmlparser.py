# -*- coding: utf-8 -*-
import logging

from tater import Node, matches, RegexLexer, Rule, parse, Token


class Tokenizer(RegexLexer):
    DEBUG = logging.INFO

    re_skip = r'[\s]+'

    r = Rule
    t = Token
    tokendefs = {
        'root': [
            r(t.OpenAngle, '<', 'element'),
            r(t.Text, r'[^<]+')
            ],

        'element': [
            r(t.Tagname, r'(?i)[a-z][\w+\-]+',
              push=('element_self_closing', 'attrs')),
            r(t.ForwardSlash, r'/'),
            ],

        'element_self_closing': [
            r(t.ForwardSlash, r'/', pop=True)
            ],

        'attrs': [
            r(t.CloseAngle, '>', pop=3)
            ],
        }


t = Token


class Text(Node):
    pass


class Element(Node):

    @property
    def tagname(self):
        _, _, text = self.items[-1]
        return text

    @matches(t.CloseAngle)
    def start_element(self, *items):
        return self

    @matches(t.Text)
    def handle_text(self, *items):
        return self.append(Text(items))

    @matches(t.OpenAngle, t.ForwardSlash, t.Tagname, t.CloseAngle)
    def end_element(self, *items):
        _, _, tagname = items[2]
        assert tagname == self.tagname
        return self.parent

    @matches(t.OpenAngle, t.Tagname, t.CloseAngle)
    def start_element(self, *items):
        items = items[1:-1]
        return self.descend(Element, items)


def main():
    import pprint
    s = ("<html><head><title>test</title></head><body><h1>page title</h1></body></html>")
    items = list(Tokenizer(s))
    pprint.pprint(items)
    x = parse(Element, items)
    x.pprint()

if __name__ == '__main__':
    main()
