import logging

from tater.core import ItemStream
from tater import Token


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
            node = node.resolve(itemstream)
        except StopIteration:
            break
    return node.getroot()
