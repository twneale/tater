import collections


Rule = collections.namedtuple('Rule', 'token rgxs push pop swap')


class Rule(Rule):
    '''Rule(token, rgxs, push, pop, swap). Subclassed in order
    to enable default args to __init__.
    '''

    def __new__(_cls, token, rgxs, push=None, pop=None, swap=None):
        'Create new instance of Rule(token, rgxs, push, pop, swap)'
        return tuple.__new__(_cls, (token, rgxs, push, pop, swap))


def bygroups(*tokens):
    '''A noop function to indicate that specified tokens should
    be applied to MatchObject groups.
    '''
    return tokens


class include(str):
    '''Indicates that a state should include rules from another state.
    '''
    pass
