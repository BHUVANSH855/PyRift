"""
Coverage tests for new rules CPY064-CPY077 and PPY048-PPY053.
Targets specific uncovered branches in each new rule.
"""
from __future__ import annotations

import ast
import textwrap


def run(rule_class, src: str) -> list:
    rule = rule_class()
    return rule.check(ast.parse(textwrap.dedent(src)), "<test>")


# CPY064 — line 46: ast.Name usage (e.g. isinstance(x, ast.Num))
class TestCPY064Extended:
    def test_ast_name_deprecated_node(self):
        from pyrift.rules.cpython.cpy064_ast_deprecated_nodes import (
            AstDeprecatedNodesRule,
        )
        # ast.Num as a Name (not attribute)
        src = "isinstance(x, ast.Num)"
        findings = run(AstDeprecatedNodesRule, src)
        assert len(findings) >= 1

    def test_clean_ast_attribute(self):
        from pyrift.rules.cpython.cpy064_ast_deprecated_nodes import (
            AstDeprecatedNodesRule,
        )
        findings = run(AstDeprecatedNodesRule, "x = ast.parse(src)")
        assert len(findings) == 0


# CPY067 — line 55: NamedTuple with less than 1 arg
class TestCPY067Extended:
    def test_namedtuple_no_args(self):
        from pyrift.rules.cpython.cpy067_typing_namedtuple_keyword import (
            TypingNamedTupleKeywordRule,
        )
        # NamedTuple() with no args - not flagged (no name)
        findings = run(TypingNamedTupleKeywordRule, "NamedTuple()")
        assert findings is not None  # no crash

    def test_namedtuple_keyword_fields(self):
        from pyrift.rules.cpython.cpy067_typing_namedtuple_keyword import (
            TypingNamedTupleKeywordRule,
        )
        findings = run(TypingNamedTupleKeywordRule, "NamedTuple('Point', x=int, y=int)")
        assert len(findings) >= 1

    def test_namedtuple_tuple_fields_not_flagged(self):
        from pyrift.rules.cpython.cpy067_typing_namedtuple_keyword import (
            TypingNamedTupleKeywordRule,
        )
        findings = run(TypingNamedTupleKeywordRule, "NamedTuple('Point', [('x', int)])")
        assert len(findings) == 0


# CPY072 — line 51: importlib.abc attribute pattern
class TestCPY072Extended:
    def test_importlib_abc_attribute(self):
        from pyrift.rules.cpython.cpy072_importlib_abc_resource import (
            ImportlibAbcResourceRule,
        )
        src = "import importlib.abc\nx = importlib.abc.ResourceReader"
        findings = run(ImportlibAbcResourceRule, src)
        assert len(findings) >= 1

    def test_clean_other_importlib_attr(self):
        from pyrift.rules.cpython.cpy072_importlib_abc_resource import (
            ImportlibAbcResourceRule,
        )
        findings = run(ImportlibAbcResourceRule, "importlib.import_module('os')")
        assert len(findings) == 0


# CPY075 — line 49: http.server.CGIHTTPRequestHandler
class TestCPY075Extended:
    def test_http_server_cgi_from_import(self):
        from pyrift.rules.cpython.cpy075_http_server_cgi import HttpServerCGIHandlerRule
        findings = run(HttpServerCGIHandlerRule, "from http.server import CGIHTTPRequestHandler")
        assert len(findings) >= 1


# CPY077 — line 52: TypedDict with less than 1 arg
class TestCPY077Extended:
    def test_typeddict_no_args(self):
        from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
            TypingTypedDictFunctionalRule,
        )
        findings = run(TypingTypedDictFunctionalRule, "TypedDict()")
        assert findings is not None  # no crash

    def test_typeddict_dict_form_valid(self):
        from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
            TypingTypedDictFunctionalRule,
        )
        # Dict form is still valid — should NOT be flagged
        findings = run(TypingTypedDictFunctionalRule, "TypedDict('Point', {'x': int})")
        assert len(findings) == 0

    def test_typeddict_zero_field_flagged(self):
        from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
            TypingTypedDictFunctionalRule,
        )
        findings = run(TypingTypedDictFunctionalRule, "TypedDict('Name')")
        assert len(findings) >= 1

    def test_typeddict_tuple_form_not_flagged(self):
        from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
            TypingTypedDictFunctionalRule,
        )
        findings = run(TypingTypedDictFunctionalRule, "TypedDict('Point', [('x', int)])")
        assert len(findings) == 0


# PPY052 — line 66: importlib.abc attribute pattern
class TestPPY052Extended:
    def test_importlib_abc_attribute_pypy(self):
        from pyrift.rules.pypy.ppy052_importlib_abc import ImportlibAbcPyPyRule
        src = "import importlib.abc\nx = importlib.abc.ResourceReader"
        findings = run(ImportlibAbcPyPyRule, src)
        assert findings is not None  # no crash


# PPY053 — line 43: lru_cache call form detection
class TestPPY053Extended:
    def test_lru_cache_call_form(self):
        from pyrift.rules.pypy.ppy053_lru_cache_thread_safety import (
            LruCacheThreadSafetyRule,
        )
        src = """
import functools

@functools.lru_cache(maxsize=128)
def expensive(x):
    return x * 2
"""
        findings = run(LruCacheThreadSafetyRule, src)
        assert len(findings) >= 1

    def test_lru_cache_bare_decorator(self):
        from pyrift.rules.pypy.ppy053_lru_cache_thread_safety import (
            LruCacheThreadSafetyRule,
        )
        src = """
from functools import lru_cache

@lru_cache
def expensive(x):
    return x * 2
"""
        findings = run(LruCacheThreadSafetyRule, src)
        assert len(findings) >= 1

    def test_lru_cache_call_no_parens(self):
        from pyrift.rules.pypy.ppy053_lru_cache_thread_safety import (
            LruCacheThreadSafetyRule,
        )
        # lru_cache() called as function (not decorator)
        findings = run(LruCacheThreadSafetyRule, "cached_fn = lru_cache(fn)")
        assert findings is not None  # no crash

    def test_clean_other_cache(self):
        from pyrift.rules.pypy.ppy053_lru_cache_thread_safety import (
            LruCacheThreadSafetyRule,
        )
        findings = run(LruCacheThreadSafetyRule, "@cache\ndef f(): pass")
        assert len(findings) == 0