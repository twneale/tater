

def parse(start, itemiter):
    '''Supply a user-defined start class.
    '''
    itemstream = ItemStream(itemiter)

    node = start()
    while 1:
        try:
            node = node.resolve(itemstream)
        except StopIteration:
            break
    return node.getroot()
