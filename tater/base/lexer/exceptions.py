
class IncompleteLex(Exception):
    '''Raised if the lexer couldn't consume all the input.
    '''


class BogusIncludeError(Exception):
    '''Raised if the lexer tries to ``include`` a nonexistent state.
    '''