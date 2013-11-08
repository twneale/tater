import re
from operator import methodcaller

from tater.base.node import ParseError
from tater.core.visitors import get_span


__all__ = ["Scanner"]


class Scanner(object):
    '''This object tries uses the hook functions defined
    in get_hooks to find points within the input string
    at which to begin lexing with the provided lexer.
    The resulting token streams are resolved against the
    object provided by get_startnode. Iterating over
    the instance yields a sequence of parse trees.
    '''
    hooks = None
    lexer = None
    debug = False

    # If true, begin lexing after the end index of the
    # scanner match objects.
    skip_match = False

    def get_hooks(self):
        '''Yields a regex used to find positions in the input string
        to begin lexing from.
        '''
        raise NotImplementedError

    def get_startnode(self):
        '''Get a node to start at. Called once per tree.
        '''
        raise NotImplementedError

    def __init__(self, text, pos=0, lexer=None):
        self.text = text
        self.pos = pos
        self.lexer = self.lexer or lexer
        self.hooks = self.hooks or list(self.get_hooks())

    def __iter__(self):
        '''Yield parse trees.
        '''
        for matchobj in self.matches_ordered():
            if not self.check_matchobj(matchobj):
                continue
            tree = self.get_tree(matchobj)
            if tree is None:
                continue
            start, end = get_span(tree)

            # Skip itemless trees.
            if None in (start, end):
                continue
            self.pos = end
            yield tree

    def check_matchobj(self, matchobj):
        if self.pos <= matchobj.start():
            # This match
            self.pos = matchobj.start()
            return True
        else:
            # This match occurred within previous text.
            return False

    def iter_matches(self):
        for hook in self.hooks:
            for matchobj in re.finditer(hook, self.text):
                yield matchobj

    def matches_ordered(self):
        return sorted(self.iter_matches(), key=methodcaller('start'))

    def handle_parse_error(self, start_node, exc):
        raise exc

    def get_tree(self, matchobj):
        if self.skip_match:
            start_pos = matchobj.end()
        else:
            start_pos = self.pos
        start = self.get_startnode(matchobj)
        tree = None
        try:
            # parse should return None if there're no input items.
            items = list(self.lexer(self.text, pos=start_pos))
            # pprint.pprint(items)
            tree = start.parse(items)
        except ParseError as exc:
            self.handle_parse_error(start, exc)

        return tree


# class Scanner(BaseScanner):
#     '''The scanner that searches for absolute citations.
#     '''
#     lexer = Lexer

#     def get_hooks(self):
#         '''Return the primary hook regex for the citation scan.
#         '''
#         database_ids = map(methodcaller('upper'), settings.DATABASE_IDS)
#         for rgx in regexes + database_ids:
#             yield '\d+\s+' + rgx

#             # R. v. Brezack, [1949] O.R. 888, [1950] 2 D.L.R. 265,
#             yield '[\(\[]\d{4}[\)\]],?\s+' + rgx
#             yield '[\(\[]\d{4}[\)\]],?\s+\d+\s+' + rgx

#             # [1861-73] All E.R. Rep. 157
#             yield '[\(\[]\d+\S+?[\)\]],?\s+' + rgx

#     def get_startnode(self, matchobj):
#         return get_startnode()

#     def handle_parse_error(self, start_node, exc):
#         start_node.getroot().pprint()
#         raise exc
