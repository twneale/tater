"""
From pygments: https://bitbucket.org/birkenfeld/pygments-main/

Copyright (c) 2006-2012 by the respective authors (see AUTHORS file).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
import unittest

<<<<<<< HEAD
from tater.tokentype import _TokenType, Token as t, is_token_subtype
=======
from tater.core.tokentype import _TokenType, Token as t, is_token_subtype
>>>>>>> org


class TokenTest(unittest.TestCase):

    def test_tokentype(self):
        e = self.assertEqual

        e(t.Cephalopod.Squid.Humboldt.split(),
          [t, t.Cephalopod,
           t.Cephalopod.Squid,
           t.Cephalopod.Squid.Humboldt])

        e(type(t.Cephalopod.Squid.Humboldt), _TokenType)

    def test_functions(self):
        self.assertTrue(is_token_subtype(t.String, t.String))
        self.assertTrue(is_token_subtype(t.Carb.Tater, t.Carb))
        self.assertFalse(is_token_subtype(t.Literal, t.String))
