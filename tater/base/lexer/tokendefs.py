import re
import functools
from collections import defaultdict

from tater.base.lexer.utils import include, Rule
from tater.base.lexer.exceptions import BogusIncludeError


class _BaseCompiler(object):
    _re_type = type(re.compile(''))

    def __init__(self, cls):
        self.cls = cls
        self.tokendefs = cls.tokendefs
        self.compiled = defaultdict(list)

    def re_compile(self, flags, text, re_compile=re.compile):
        raise NotImplementedError()

    def _process_rules(self, state, rules):
        flags = getattr(self.cls, 'flags', 0)
        rubberstamp = lambda s: s
        re_compile = functools.partial(self.re_compile, flags)
        getfunc = {
            unicode: re_compile,
            str: re_compile,
            self._re_type: rubberstamp
            }

        append = self.compiled[state].append
        iter_rgxs = self._iter_rgxs

        for rule in rules:
            if isinstance(rule, include):
                try:
                    rules = self.tokendefs[rule]
                except KeyError:
                    msg = (
                        "Can't include undefined state %r. Did you forget "
                        "do define the state %r in your lexer?")
                    raise BogusIncludeError(msg % (rule, rule))
                self._process_rules(state, rules)
                continue

            rule = Rule(*rule)

            _rgxs = []
            _append = _rgxs.append

            for rgx, type_ in iter_rgxs(rule):
                func = getfunc[type_](rgx)
                _append(func)

            rgxs = _rgxs
            rule = rule._replace(rgxs=rgxs)
            append(rule)

    def compile_all(self):
        '''Compile the tokendef regexes.
        '''
        for state, rules in self.tokendefs.items():
            self._process_rules(state, rules)
        return self.compiled

    def _iter_rgxs(self, rule, _re_type=_re_type):
        rgx = rgxs = rule.rgxs
        rgx_type = type(rgx)
        if issubclass(rgx_type, (basestring, _re_type)):
            yield rgx, rgx_type
        else:
            for rgx in rgxs:
                rgx_type = type(rgx)
                yield rgx, rgx_type


class Compiler(_BaseCompiler):
    def re_compile(self, flags, text, re_compile=re.compile):
        return re.compile(text, flags).match


class DebugCompiler(_BaseCompiler):
    def re_compile(self, flags, text, re_compile=re.compile):
        return re.compile(text, flags)

