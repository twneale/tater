from operator import itemgetter

from tater.utils.trie import Trie
from tater.base.dispatcher import Dispatcher


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


tokenseq = TokentypeSequence()