from operator import itemgetter

from tater.utils.trie import Trie
from tater.base.dispatcher import Dispatcher
from tater.core.tokentype import string_to_tokentype


class DispatchUserError(Exception):
    '''Raised when user invokes a dispatcher incorrectly.
    '''


class TokentypeSequence(Dispatcher):
    '''A basic dispatcher that matches sequences of tokentypes
    in the itemstream against a state machine in order to resolve
    to stream to a handler method in each state.
    '''
    def prepare(self, dispatch_data):
        trie = Trie()
        for signature, method in dispatch_data.items():
            tokenseq, kwargs = self.loads(signature)
            trie.add(tokenseq, method)
        return trie

    def dispatch(self, itemstream, dispatch_data, second=itemgetter(1)):
        '''Try to find a handler that matches the signatures registered
        to this dispatcher instance.
        '''
        match = dispatch_data.scan(itemstream)
        if match:
            return match.value(), match.group()


class TokenSubtypes(Dispatcher):
    '''Will match at most one subtype of the given token type.
    '''
    def prepare(self, dispatch_data):
        str2token = string_to_tokentype
        for signature, method in dispatch_data.items():
            data = {}
            args, kwargs = self.loads(signature)
            if 1 < len(args):
                msg = ('The %s dispatcher only accepts one '
                       'token as an argument; got %d')
                cls_name = self.__class__.__name__
                raise DispatchUserError(msg % (cls_name, len(args)))

            token = args[0]
            data[str2token(token)] = method
        return data


    def dispatch(self, itemstream, dispatch_data, str2token=string_to_tokentype):
        item = itemstream.this()
        item_token = str2token(item.token)
        for match_token, method in dispatch_data.items():
            if item_token in match_token:
                return method, [next(itemstream)]
        return

matches_subtypes = token_subtypes = TokenSubtypes()
matches = tokenseq = TokentypeSequence()