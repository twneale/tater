import re


_translate_chars = [
    ("([.,:;'`\[\]()])", '{1}?'),
    ('\s+', ' {,3}'),
    ]


def liberalizer(string):
    print repr(string)
    subber = lambda m: ' ?{0}? ?'.format(m.group())
    string = re.sub("[.,:;'`\[\]()]", subber, string)
    string = re.sub('\s+', '\s{,3}', string)
    return string


def trie2regex(trie):

    def _add_node(node, buf):
        keys = filter(None, node.keys())
        keys_len = len(keys)
        if 1 < keys_len:
            buf.append('(?:')

        for i, char in enumerate(keys):
            buf.append(char)
            v = node[char]
            if isinstance(v, dict):
                _add_node(node[char], buf)
            if i < (keys_len - 1):
                buf.append('|')

        if 1 < keys_len:
            buf.append(')')

    buf = []
    _add_node(trie, buf)
    return ''.join(buf)


def add(trie, terms, terminus=None, skipchars=[],
        preprocessors=[]):

    res = trie

    for s in terms:

        this = res
        s_len = len(s) - 1

        for func in preprocessors:
            s = func(s)

        for i, c in enumerate(s):

            if c in skipchars:
                continue

            try:
                this = this[c]
            except KeyError:
                this[c] = {}
                this = this[c]

            if i == s_len:
                this[0] = terminus

    return res


def build_regex(terms, liberalize=True):
    trie = {}
    if liberalize:
        terms = map(liberalizer, terms)
    trie = add(trie, terms)
    return trie2regex(trie)
