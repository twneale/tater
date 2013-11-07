import logging

from tater.core.tokentype import Token
from tater.utils.itemstream import ItemStream


def parse(start, itemiter, DEBUG=None):
    '''Supply a user-defined start class.
    '''
    itemstream = ItemStream(itemiter)

    if callable(start):
        node = start()
    else:
        node = start

    while 1:
        try:
            if DEBUG == logging.DEBUG:
                print '%r <-- %r' % (node, itemstream)
                node.getroot().pprint()
            node = node.resolve(itemstream)
        except StopIteration:
            break
    return node.getroot()
