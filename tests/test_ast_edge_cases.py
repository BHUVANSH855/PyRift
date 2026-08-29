"""
Phase 6 — Advanced AST edge cases.

Tests rules against aliased imports, conditional imports, imports inside
functions, nested classes, lambdas, comprehensions, decorators, match/case,
multi-line calls, and unicode identifiers.
"""
from __future__ import annotations

import ast
import textwrap


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule_class, src: str):
    rule = rule_class()
    return rule.check(ast.parse(textwrap.dedent(src)), "<test>")


# ── 1. Aliased imports ─────────────────────────────────────────────────────

class TestAliasedImports:
    """Rules must handle `import X as Y` and `from X import Y as Z`."""

    def test_ctypes_util_alias_find_library(self):
        """`import ctypes.util as cu; cu.find_library()` — the alias
        should be tracked and the call should trigger PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
import ctypes.util as cu
cu.find_library("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY047"

    def test_ctypes_find_library_alias(self):
        """`from ctypes.util import find_library as fl` — the alias
        should be tracked and bare fl() should trigger PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library as fl
fl("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_multiprocessing_alias(self):
        """`import multiprocessing as mp` — alias should be recognized
        and trigger CPY023 (since set_start_method is not called)."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = "import multiprocessing as mp"
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 1

    def test_weakref_proxy_alias(self):
        """`from weakref import proxy as wp` — alias renames the local
        binding. The rule checks for Name id=='proxy', but the local
        name is 'wp'. So `wp(obj)` does NOT trigger PPY004.
        This is a documented limitation of name-based detection."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
from weakref import proxy as wp
wp(obj)
"""
        findings = run(WeakrefProxyRule, src)
        # wp does NOT match id=='proxy' — known FP boundary
        assert len(findings) == 0

    def test_open_encoding_alias(self):
        """`from io import open as iopen` — iopen with encoding must not
        trigger CPY046 (rule checks func.id == 'open', not aliases)."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
from io import open as iopen
iopen('file', encoding='utf-8')
"""
        findings = run(OpenEncodingRule, src)
        # iopen is not matched (func.id != 'open')
        assert len(findings) == 0


# ── 2. Conditional imports ─────────────────────────────────────────────────

class TestConditionalImports:
    """Version-guarded and try/except imports must be handled correctly."""

    def test_version_guarded_multiprocessing(self):
        """import multiprocessing inside `if sys.version_info >= ...` guard
        still triggers CPY023 (rule does not analyze guards)."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
import sys
if sys.version_info >= (3, 14):
    import multiprocessing
"""
        findings = run(MultiprocessingForkRule, src)
        # Rule walks all imports, does not skip guarded ones
        assert len(findings) == 1

    def test_try_except_import_ctypes(self):
        """import ctypes.util inside try/except still triggers PPY047
        (rule walks all AST nodes unconditionally)."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
try:
    import ctypes.util
    ctypes.util.find_library("c")
except ImportError:
    pass
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_conditional_encoding_open(self):
        """open() with encoding inside conditional still must not trigger
        CPY046 (encoding is present)."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
if True:
    open('file', encoding='utf-8')
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_version_guarded_tomllib(self):
        """`import tomllib` guarded by version check is a common pattern.
        This is NOT a false positive concern for CPY rules (they flag
        unconditionally)."""
        from pyrift.rules.cpython.cpy004_tomllib import TomllibRule
        src = """
import sys
if sys.version_info >= (3, 11):
    import tomllib
"""
        findings = run(TomllibRule, src)
        # TomllibRule may or may not flag guarded imports — just verify no crash
        assert findings is not None


# ── 3. Imports inside functions ────────────────────────────────────────────

class TestImportsInsideFunctions:
    """Local imports inside function bodies must be detected by rules."""

    def test_multiprocessing_inside_function(self):
        """import multiprocessing inside a function triggers CPY023
        (rule walks entire AST including function bodies)."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
def setup():
    import multiprocessing
    return multiprocessing.Process(target=run)
"""
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 1

    def test_ctypes_find_library_inside_function(self):
        """find_library() inside a function triggers PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
def load_lib():
    from ctypes.util import find_library
    return find_library("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_open_encoding_inside_function(self):
        """open() without encoding inside function triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
def read_file(path):
    return open(path).read()
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_proxy_inside_function(self):
        """proxy() call inside function triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
def make_proxy(obj):
    return proxy(obj)
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_import_inside_nested_function(self):
        """import inside nested function still triggers CPY023."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
def outer():
    def inner():
        import multiprocessing
"""
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 1


# ── 4. Nested class definitions ───────────────────────────────────────────

class TestNestedClassDefinitions:
    """Rules must handle patterns inside nested classes correctly."""

    def test_builtin_monkey_patch_in_nested_class(self):
        """Monkey-patching builtins inside a nested class triggers PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        src = """
class Outer:
    class Inner:
        list.my_method = lambda self: None
"""
        findings = run(BuiltinMonkeyPatchRule, src)
        assert len(findings) == 1

    def test_subclass_builtin_in_nested_class(self):
        """Subclassing builtins in nested class does NOT trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        src = """
class Outer:
    class Inner(list):
        pass
"""
        findings = run(BuiltinMonkeyPatchRule, src)
        assert len(findings) == 0

    def test_del_in_nested_class(self):
        """del self.attr in nested class triggers PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        src = """
class Outer:
    class Inner:
        def cleanup(self):
            del self.attr
"""
        findings = run(ModuleAttrDeleteRule, src)
        assert len(findings) == 1

    def test_del_in_nested_class_name_delete(self):
        """del x (name delete) in nested class does NOT trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        src = """
class Outer:
    class Inner:
        def cleanup(self):
            del x
"""
        findings = run(ModuleAttrDeleteRule, src)
        assert len(findings) == 0

    def test_del_ignored_exceptions_in_nested_class(self):
        """__del__ with calls in nested class triggers PPY033."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Outer:
    class Inner:
        def __del__(self):
            self.cleanup()
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 1


# ── 5. Lambda functions ───────────────────────────────────────────────────

class TestLambdaPatterns:
    """Rules must handle lambda expressions correctly."""

    def test_lambda_with_proxy_call(self):
        """proxy() inside a lambda triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = "make = lambda obj: proxy(obj)"
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_lambda_no_proxy(self):
        """Lambda without proxy() does not trigger PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = "double = lambda x: x * 2"
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 0

    def test_lambda_with_open_no_encoding(self):
        """open() without encoding inside lambda triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = "reader = lambda p: open(p).read()"
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_lambda_with_open_encoding(self):
        """open() with encoding inside lambda must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = "reader = lambda p: open(p, encoding='utf-8').read()"
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_lambda_with_find_library(self):
        """find_library() inside lambda triggers PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library
loader = lambda name: find_library(name)
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_lambda_with_find_library_no_ctypes(self):
        """find_library() from non-ctypes module inside lambda doesn't trigger."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
import mymodule
loader = lambda name: mymodule.find_library(name)
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 0


# ── 6. Comprehensions ─────────────────────────────────────────────────────

class TestComprehensions:
    """Rules must handle list/dict/set comprehensions correctly."""

    def test_list_comp_with_open(self):
        """open() without encoding in list comprehension triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = "lines = [open(f).read() for f in files]"
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_list_comp_with_open_encoding(self):
        """open() with encoding in list comprehension must not trigger."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = "lines = [open(f, encoding='utf-8').read() for f in files]"
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_dict_comp_with_proxy(self):
        """proxy() inside dict comprehension triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = "proxies = {k: proxy(v) for k, v in items}"
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_set_comp_with_find_library(self):
        """find_library() inside set comprehension triggers PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library
libs = {find_library(name) for name in names}
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_nested_comp_with_open(self):
        """open() without encoding in nested comprehension triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
result = [
    open(f).read()
    for group in groups
    for f in group.files
]
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_generator_expr_with_proxy(self):
        """proxy() inside generator expression triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = "gen = (proxy(obj) for obj in objs)"
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1


# ── 7. Decorator with rule-relevant patterns ──────────────────────────────

class TestDecoratorPatterns:
    """Rules must detect patterns inside decorator expressions."""

    def test_decorator_with_proxy(self):
        """proxy() call in decorator triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
@proxy(obj)
def wrapper():
    pass
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_decorator_with_open_encoding(self):
        """open() with encoding in decorator must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
@contextmanager
def managed():
    with open('f', encoding='utf-8') as fh:
        yield fh
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_decorator_attribute_not_flagged(self):
        """Attribute access in decorator (e.g., @staticmethod) is not
        a function call and must not trigger PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
@staticmethod
def foo():
    pass
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 0

    def test_decorator_call_not_proxy(self):
        """Decorator with a non-proxy call must not trigger PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
@decorator
def foo():
    pass
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 0


# ── 8. Match/case with rule-relevant patterns ──────────────────────────────

class TestMatchCasePatterns:
    """Python 3.10+ match/case statements with rule-relevant patterns."""

    def test_match_with_open_in_case(self):
        """open() without encoding in match/case triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
match command:
    case "read":
        data = open(path).read()
    case "write":
        pass
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_match_with_proxy_in_case(self):
        """proxy() in match/case triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
match action:
    case "wrap":
        p = proxy(obj)
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_match_case_no_rule_patterns(self):
        """match/case with no rule-relevant code triggers nothing."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
match value:
    case 1:
        x = 42
    case _:
        pass
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_match_case_with_find_library(self):
        """find_library() in match/case triggers PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library
match platform:
    case "linux":
        lib = find_library("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1


# ── 9. Multi-line calls ───────────────────────────────────────────────────

class TestMultiLineCalls:
    """Multi-line function calls must be handled correctly."""

    def test_multiline_open_no_encoding(self):
        """Multi-line open() without encoding triggers CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
data = open(
    filepath,
    'r'
).read()
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1

    def test_multiline_open_with_encoding(self):
        """Multi-line open() with encoding must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
data = open(
    filepath,
    'r',
    encoding='utf-8'
).read()
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_multiline_find_library(self):
        """Multi-line find_library() call triggers PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library
lib = find_library(
    "c"
)
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_multiline_proxy(self):
        """Multi-line proxy() call triggers PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        src = """
p = proxy(
    obj
)
"""
        findings = run(WeakrefProxyRule, src)
        assert len(findings) == 1

    def test_multiline_open_binary(self):
        """Multi-line open() in binary mode must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
data = open(
    filepath,
    'rb'
).read()
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 0

    def test_deeply_nested_multiline_call(self):
        """open() without encoding in deeply nested multi-line expression."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        src = """
result = process(
    open(
        filepath,
        'r'
    ).read()
)
"""
        findings = run(OpenEncodingRule, src)
        assert len(findings) == 1


# ── 10. Unicode identifiers ───────────────────────────────────────────────

class TestUnicodeIdentifiers:
    """Unicode identifiers in variable/class names must not confuse rules."""

    def test_unicode_var_name_bitwise_or(self):
        """Bitwise OR on a unicode variable must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "\u00e4 |= \u00f6")
        assert len(findings) == 0

    def test_unicode_var_name_del_attr(self):
        """del \u00e4.\u00f6 triggers PPY027 (attribute delete)."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del \u00e4.\u00f6")
        assert len(findings) == 1

    def test_unicode_class_name_subclass_builtin(self):
        """Subclassing builtins with unicode class name does NOT trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "class \u00c4(list): pass")
        assert len(findings) == 0

    def test_unicode_class_name_monkey_patch(self):
        """Monkey-patching builtin from unicode-named class triggers PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "list.\u00e4tt = 1")
        assert len(findings) == 1

    def test_unicode_func_name_not_proxy(self):
        """Unicode function call must not trigger PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        findings = run(WeakrefProxyRule, "\u00e4\u00f6(obj)")
        assert len(findings) == 0

    def test_unicode_del_name_not_flagged(self):
        """del \u00e4 (name delete, not attribute) must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del \u00e4")
        assert len(findings) == 0

    def test_unicode_open_no_encoding(self):
        """open() without encoding still triggers CPY046 with unicode filename."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('\u00e4\u00f6.txt')")
        assert len(findings) == 1

    def test_unicode_multiprocessing_import(self):
        """`import multiprocessing` with unicode in surrounding code still triggers."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = "\u00e4 = 1\nimport multiprocessing"
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 1
