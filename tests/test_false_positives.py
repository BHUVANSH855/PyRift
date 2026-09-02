"""
Phase 5 — False-positive test suite.

Systematically proves detector precision for the highest-risk rules.
Each test verifies that benign patterns do NOT trigger findings.
"""
from __future__ import annotations

import ast
import textwrap


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule_class, src: str):
    rule = rule_class()
    return rule.check(ast.parse(textwrap.dedent(src)), "<test>")


# ── CPY041 — dict merge |= operator ────────────────────────────────────────

class TestCPY041FalsePositives:
    """CPY041 flags dict merge |= when the target name looks dict-like.
    Bitwise OR augmented assignment on ints, sets, flags must NOT trigger."""

    def test_flags_bitwise_or(self):
        """Bitwise OR on flags (common pattern) must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "flags |= FLAG_A")
        assert len(findings) == 0

    def test_set_bitwise_or(self):
        """Set union via |= must not trigger CPY041 (sets, not dicts)."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "set1 |= set2")
        assert len(findings) == 0

    def test_int_bitwise_or(self):
        """Integer bitwise OR must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "x |= 1")
        assert len(findings) == 0

    def test_permission_bitwise_or(self):
        """Permission flag accumulation must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "perms |= READ | WRITE")
        assert len(findings) == 0

    def test_counter_bitwise_or(self):
        """Counter variable with non-dict-like name must not trigger."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "counter |= 0x01")
        assert len(findings) == 0

    def test_mask_bitwise_or(self):
        """Bitmask operations must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "mask |= (1 << 8)")
        assert len(findings) == 0

    def test_binop_two_names_no_dict_literal(self):
        """Name | Name without dict literal must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "result = a | b")
        assert len(findings) == 0

    def test_binop_int_and_name(self):
        """Int | Name must not trigger CPY041."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "result = 0xFF | flags")
        assert len(findings) == 0

    def test_binop_set_literal(self):
        """Set literal | Name must not trigger CPY041 (only dict literals)."""
        from pyrift.rules.cpython.cpy041_dict_merge_operator import (
            DictMergeOperatorRule,
        )
        findings = run(DictMergeOperatorRule, "result = {1, 2} | other")
        assert len(findings) == 0


# ── CPY046 — open() encoding ───────────────────────────────────────────────

class TestCPY046FalsePositives:
    """CPY046 flags open() in text mode without encoding=.
    open() with explicit encoding or binary mode must NOT trigger."""

    def test_explicit_encoding(self):
        """open() with encoding='utf-8' must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', encoding='utf-8')")
        assert len(findings) == 0

    def test_binary_mode(self):
        """open() in binary mode ('rb') must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', 'rb')")
        assert len(findings) == 0

    def test_binary_write_mode(self):
        """open() in binary write mode ('wb') must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', 'wb')")
        assert len(findings) == 0

    def test_binary_mode_kwarg(self):
        """open() with mode='rb' as keyword arg must not trigger."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', mode='rb')")
        assert len(findings) == 0

    def test_explicit_encoding_with_mode(self):
        """open() with both mode and encoding must not trigger."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', 'r', encoding='latin-1')")
        assert len(findings) == 0

    def test_stdout_reference(self):
        """open() on sys.stdout must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open(sys.stdout)")
        assert len(findings) == 0

    def test_stdin_reference(self):
        """open() on sys.stdin must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open(sys.stdin)")
        assert len(findings) == 0

    def test_stderr_reference(self):
        """open() on sys.stderr must not trigger CPY046."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open(sys.stderr)")
        assert len(findings) == 0

    def test_append_binary_mode(self):
        """open() in append binary mode ('ab') must not trigger."""
        from pyrift.rules.cpython.cpy046_open_encoding import OpenEncodingRule
        findings = run(OpenEncodingRule, "open('file', 'ab')")
        assert len(findings) == 0


# ── PPY004 — weakref.proxy() ──────────────────────────────────────────────

class TestPPY004FalsePositives:
    """PPY004 flags calls named proxy(). User-defined proxy functions
    that are NOT weakref.proxy must not trigger, but the rule is
    intentionally broad (matches any `proxy()` call)."""

    def test_user_defined_proxy_function(self):
        """A bare proxy() call without a weakref import is not enough
        evidence that the call refers to weakref.proxy()."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        findings = run(WeakrefProxyRule, "proxy(obj)")
        assert len(findings) == 0

    def test_proxy_method_on_non_weakref_object(self):
        """A .proxy() method on an unrelated object is not weakref.proxy()."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule

        findings = run(WeakrefProxyRule, "my_obj.proxy()")
        assert len(findings) == 0

    def test_not_flagged_without_proxy_call(self):
        """Code that does not call proxy() must not trigger PPY004."""
        from pyrift.rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
        findings = run(WeakrefProxyRule, "x = weakref.ref(obj)")
        assert len(findings) == 0


# ── PPY006 — builtin monkey-patch ─────────────────────────────────────────

class TestPPY006FalsePositives:
    """PPY006 flags `BUILTIN_TYPE.attr = value` assignments.
    Subclassing builtins must NOT trigger (different AST node)."""

    def test_subclassing_list(self):
        """Subclassing list must not trigger PPY006 (ClassDef, not Assign)."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "class MyList(list): pass")
        assert len(findings) == 0

    def test_subclassing_dict(self):
        """Subclassing dict must not trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "class MyDict(dict): pass")
        assert len(findings) == 0

    def test_subclassing_str(self):
        """Subclassing str must not trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "class MyStr(str): pass")
        assert len(findings) == 0

    def test_non_builtin_attr_set(self):
        """Setting attr on a non-builtin object must not trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "my_obj.method = lambda: None")
        assert len(findings) == 0

    def test_non_builtin_subscript_set(self):
        """Dict subscript assignment must not trigger PPY006."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "d['key'] = 'value'")
        assert len(findings) == 0

    def test_user_class_attr_set(self):
        """Setting attr on user-defined class instance must not trigger."""
        from pyrift.rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
        findings = run(BuiltinMonkeyPatchRule, "obj.attr = 42")
        assert len(findings) == 0


# ── PPY027 — module attr delete ────────────────────────────────────────────

class TestPPY027FalsePositives:
    """PPY027 flags `del obj.attr` patterns. Normal instance attribute
    deletion on `self` should not be the concern (but the rule is INFO
    and broad). We test that non-attribute deletes don't trigger."""

    def test_del_variable(self):
        """`del x` (name delete, not attribute) must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del x")
        assert len(findings) == 0

    def test_del_subscript(self):
        """`del d['key']` (subscript delete) must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del d['key']")
        assert len(findings) == 0

    def test_del_slice(self):
        """`del lst[0:5]` (slice delete) must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del lst[0:5]")
        assert len(findings) == 0

    def test_del_self_attr_info_level(self):
        """`del self.attr` IS flagged by PPY027 (INFO level) — this is
        the intended behavior. We document this as NOT a false positive."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del self.attr")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY027"

    def test_del_local_var(self):
        """`del my_var` (plain name) must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "del my_var")
        assert len(findings) == 0

    def test_no_del_statement(self):
        """Code with no delete statement must not trigger PPY027."""
        from pyrift.rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
        findings = run(ModuleAttrDeleteRule, "x = 1")
        assert len(findings) == 0


# ── PPY033 — __del__ exceptions ───────────────────────────────────────────

class TestPPY033FalsePositives:
    """PPY033 flags __del__ methods that contain raise or function calls.
    __del__ with only simple assignments/returns must NOT trigger."""

    def test_del_empty_body(self):
        """`__del__` with only `pass` must not trigger PPY033."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        pass
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 0

    def test_del_only_assignment(self):
        """`__del__` with only attribute assignment must not trigger."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        self._cleaned = True
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 0

    def test_del_only_return(self):
        """`__del__` with only `return` must not trigger PPY033."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        return
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 0

    def test_del_with_raise_triggers(self):
        """`__del__` with `raise` SHOULD trigger PPY033 (not a FP)."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        raise RuntimeError("cleanup failed")
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 1

    def test_del_with_call_triggers(self):
        """`__del__` with a function call SHOULD trigger PPY033 (not a FP)."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        self.cleanup()
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 1

    def test_del_with_try_except_triggers(self):
        """`__del__` with try/except containing calls triggers PPY033
        (the rule walks nested nodes, finding the Call inside try)."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 1

    def test_non_del_method_with_calls(self):
        """A regular method with calls must not trigger PPY033."""
        from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
            DelIgnoredExceptionsRule,
        )
        src = """
class Foo:
    def close(self):
        self.cleanup()
"""
        findings = run(DelIgnoredExceptionsRule, src)
        assert len(findings) == 0


# ── PPY047 — ctypes find_library ──────────────────────────────────────────

class TestPPY047FalsePositives:
    """PPY047 flags find_library() only when it comes from ctypes.
    User-defined find_library or unrelated module calls must NOT trigger."""

    def test_user_defined_find_library(self):
        """A user-defined find_library function must not trigger PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
def find_library(name):
    return f"/usr/lib/lib{name}.so"

find_library("foo")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 0

    def test_unrelated_module_find_library(self):
        """some_module.find_library() where some_module is not ctypes
        must not trigger PPY047."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
import mymodule
mymodule.find_library("foo")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 0

    def test_method_named_find_library(self):
        """A method named find_library on a user class must not trigger."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
class Finder:
    def find_library(self, name):
        return name

f = Finder()
f.find_library("bar")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 0

    def test_ctypes_find_library_bare_import_triggers(self):
        """from ctypes.util import find_library + find_library() triggers."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
from ctypes.util import find_library
find_library("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_ctypes_util_module_attr_triggers(self):
        """import ctypes.util + ctypes.util.find_library() triggers."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        src = """
import ctypes.util
ctypes.util.find_library("c")
"""
        findings = run(CtypesFindLibraryRule, src)
        assert len(findings) == 1

    def test_string_not_flagged(self):
        """A string containing 'find_library' must not trigger."""
        from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule
        findings = run(CtypesFindLibraryRule, 'x = "find_library"')
        assert len(findings) == 0


# ── CPY023 — multiprocessing fork ─────────────────────────────────────────

class TestCPY023FalsePositives:
    """CPY023 flags `import multiprocessing` when set_start_method/get_context
    is NOT called in the same file. When those safety calls exist, no finding."""

    def test_set_start_method_suppresses(self):
        """import multiprocessing + set_start_method() must not trigger CPY023."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
import multiprocessing
multiprocessing.set_start_method('spawn')
"""
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 0

    def test_get_context_suppresses(self):
        """import multiprocessing + get_context() must not trigger CPY023."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
import multiprocessing
ctx = multiprocessing.get_context('spawn')
"""
        findings = run(MultiprocessingForkRule, src)
        assert len(findings) == 0

    def test_import_multiprocessing_alone_triggers(self):
        """import multiprocessing without safety call SHOULD trigger."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        findings = run(MultiprocessingForkRule, "import multiprocessing")
        assert len(findings) == 1

    def test_from_import_multiprocessing(self):
        """`from multiprocessing import Process` also triggers CPY023
        only for `import multiprocessing` (not from-imports)."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        findings = run(MultiprocessingForkRule, "from multiprocessing import Process")
        assert len(findings) == 0

    def test_import_submodule_not_flagged(self):
        """`import multiprocessing.pool` does NOT trigger CPY023
        (only bare `import multiprocessing` is flagged)."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        findings = run(MultiprocessingForkRule, "import multiprocessing.pool")
        assert len(findings) == 0

    def test_non_multiprocessing_import(self):
        """Importing a non-multiprocessing module must not trigger CPY023."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        findings = run(MultiprocessingForkRule, "import os")
        assert len(findings) == 0

    def test_set_start_method_on_other_module(self):
        """set_start_method() on any object suppresses CPY023 — the rule
        checks for ANY call with attr 'set_start_method', not just
        multiprocessing.set_start_method. This is documented behavior."""
        from pyrift.rules.cpython.cpy023_multiprocessing_fork import (
            MultiprocessingForkRule,
        )
        src = """
import multiprocessing
other.set_start_method('spawn')
"""
        findings = run(MultiprocessingForkRule, src)
        # Rule treats any set_start_method() call as explicit safety
        assert len(findings) == 0
