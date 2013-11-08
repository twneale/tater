
class ConfigurationError(Exception):
    '''The user-defined ast models were screwed up.
    '''


class ParseError(Exception):
    '''
    The tokens weren't matched against any suitable method
    on the current node.
    '''


class AmbiguousNodeNameError(Exception):
    '''Raised if the user was silly and used an
    ambiguous string reference to a node class.
    '''