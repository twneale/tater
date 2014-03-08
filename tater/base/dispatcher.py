import cPickle

from functools import wraps
from collections import defaultdict
from operator import itemgetter

from tater.utils import SetDefault, NoClobberDict, KeyClobberError


class DuplicateHandlerFound(Exception):
    '''Raised when someone does something silly, like
    dispatch two conlicting handlers to process the same
    stream input.
    '''


class Dispatcher(object):
    '''Implements the base functionality for dispatcher types.
    The node instances delegate their dispatch functions to
    subclasses of Dispatcher.
    '''
    __slots__ = tuple()

    def __call__(self, *args, **kwargs):
        return self._make_decorator(*args, **kwargs)

    def _make_decorator(self, *args, **kwargs):
        def decorator(method):
            self.register(method, args, kwargs)
            return method
        return decorator

    loads = cPickle.loads

    def register(self, method, args, kwargs):
        '''Given a single decorated handler function,
        prepare it for the node __new__ method.
        '''
        default = defaultdict(NoClobberDict)
        with SetDefault(method, '_disp', default) as registry:
            key = cPickle.dumps((args, kwargs))
            try:
                registry[self][key] = method
            except KeyClobberError:
                other_method = registry[type(self)][key]
                msg = (
                    "Can't register %r: previously registered handler %r "
                    "found for input signature %r.")
                args = (method, other_method, (args, kwargs))
                raise DuplicateHandlerFound(msg % args)

    def prepare(self, dispatch_data):
        '''Given all the registered handlers for this
        dispatcher instance, return any data required
        by the dispatch method. It gets stored on the
        node on which the handlers are defined.

        Can be overridden to provide more efficiency,
        simplicity, etc.
        '''
        raise NotImplementedError()

    def dispatch(self, itemstream, dispatch_data):
        '''Provides the logic for dispatching the itemstream
        to a handler function, given the dispatch_data created at
        import time.
        '''
        raise NotImplementedError()
