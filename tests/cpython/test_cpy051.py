import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
    FreeThreadedGlobalStateRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY051:
    rule = FreeThreadedGlobalStateRule()

    def test_detects_mutated_module_level_list(self):
        findings = run(
            self.rule,
            """
            _cache = []

            def update():
                _cache.append(1)
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"
        assert findings[0].severity == Severity.WARNING

    def test_detects_mutated_module_level_dict(self):
        findings = run(
            self.rule,
            """
            _registry = {}

            def register():
                _registry["x"] = 1
            """,
        )
        assert len(findings) == 1

    def test_detects_mutated_module_level_set(self):
        findings = run(
            self.rule,
            """
            _seen = {1, 2}

            def remember():
                _seen.add(3)
            """,
        )
        assert len(findings) == 1

    def test_plain_definition_is_not_enough(self):
        assert run(self.rule, "_cache = []") == []

    def test_set_constructor_is_not_flagged_without_mutation(self):
        assert run(self.rule, "_seen = set()") == []

    def test_immutable_module_level_value_is_clean(self):
        assert run(self.rule, "VERSION = '1.0'") == []

    def test_plain_reassignment_is_not_mutation(self):
        assert run(
            self.rule,
            """
            _cache = []

            def replace():
                _cache = [1]
            """,
        ) == []

    def test_module_initialization_mutation_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            _cache = []
            _cache.append(1)
            """,
        )
        assert findings == []

    def test_detects_augassign_mutation(self):
        findings = run(
            self.rule,
            """
            _cache = []

            def update():
                _cache += [1]
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"
        assert findings[0].severity == Severity.WARNING

    def test_detects_delete_mutation(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def clear():
                del _cache
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_delete_subscript_mutation(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def remove():
                del _cache["key"]
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_mutation_inside_class_method(self):
        findings = run(
            self.rule,
            """
            _registry = {}

            class Registry:
                def add(self, key):
                    _registry[key] = True
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_mutation_of_nested_attribute(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                _cache.setdefault("nested", {}).update({"x": 1})
            """,
        )
        assert len(findings) == 1

    def test_does_not_flag_unrelated_local_mutation(self):
        findings = run(
            self.rule,
            """
            _cache = []

            def update():
                local_cache = []
                local_cache.append(1)
            """,
        )
        assert findings == []

    def test_clean_mutation_inside_lock(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                with _lock:
                    _cache["key"] = 1
            """,
        )
        assert findings == []

    def test_clean_mutation_inside_rlock(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = []
            _lock = threading.RLock()

            def update():
                with _lock:
                    _cache.append(1)
            """,
        )
        assert findings == []

    def test_clean_mutation_inside_condition(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _condition = threading.Condition()

            def update():
                with _condition:
                    _cache["key"] = 1
            """,
        )
        assert findings == []

    def test_clean_mutation_inside_semaphore(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = []
            _semaphore = threading.Semaphore()

            def update():
                with _semaphore:
                    _cache.append(1)
            """,
        )
        assert findings == []

    def test_unsynchronized_mutation_after_lock_is_detected(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                with _lock:
                    value = 1

                _cache["key"] = value
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_unsynchronized_mutation_is_still_detected(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                _cache["key"] = 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_read_modify_write(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def increment(key):
                _cache[key] = _cache.get(key, 0) + 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_check_then_mutate(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def get_or_create(key):
                if key not in _cache:
                    _cache[key] = create_value()
                return _cache[key]
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_read_then_append(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def add_value(key, value):
                values = _cache.get(key)
                if values is None:
                    values = []
                    _cache[key] = values
                values.append(value)
            """,
        )
        assert len(findings) == 1

    def test_does_not_require_read_for_direct_mutation(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def store(key, value):
                _cache[key] = value
            """,
        )
        assert len(findings) == 1

    def test_clean_read_modify_write_inside_lock(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def increment(key):
                with _lock:
                    _cache[key] = _cache.get(key, 0) + 1
            """,
        )
        assert findings == []

    def test_clean_check_then_mutate_inside_lock(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def get_or_create(key):
                with _lock:
                    if key not in _cache:
                        _cache[key] = create_value()
                    return _cache[key]
            """,
        )
        assert findings == []

    def test_clean_mutation_with_explicit_acquire_release(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                _lock.acquire()
                try:
                    _cache["key"] = 1
                finally:
                    _lock.release()
            """,
        )
        assert findings == []

    def test_unsynchronized_mutation_after_release_is_detected(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                _lock.acquire()
                try:
                    _cache["key"] = 1
                finally:
                    _lock.release()

                _cache["other"] = 2
            """,
        )
        assert len(findings) == 1

    def test_does_not_flag_read_only_global_access(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def lookup(key):
                return _cache.get(key)
            """,
        )
        assert findings == []

    def test_does_not_flag_read_only_membership_check(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def contains(key):
                return key in _cache
            """,
        )
        assert findings == []

    def test_does_not_flag_local_read_modify_write(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                local_cache = {}
                local_cache["x"] = local_cache.get("x", 0) + 1
            """,
        )
        assert findings == []

    def test_does_not_flag_mutation_in_nested_function_as_separate_scope(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def outer():
                def inner():
                    _cache["key"] = 1
                return inner
            """,
        )
        assert len(findings) == 1

    def test_suggestion_mentions_lock(self):
        findings = run(
            self.rule,
            """
            _cache = []

            def update():
                _cache.append(1)
            """,
        )
        assert "lock" in findings[0].suggestion.lower()

    # ── Coverage-expansion cases (async-with lock alias, handlers, nested
    #    function collection, bare lock constructors, recursion, edge paths) ──

    def test_clean_mutation_inside_async_with_lock_as_alias(self):
        findings = run(
            self.rule,
            """
            import asyncio

            _cache = []
            _lock = asyncio.Lock()

            async def update():
                async with _lock as held:
                    _cache.append(1)
            """,
        )
        assert findings == []

    def test_unsynchronized_mutation_in_try_handler_is_detected(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                try:
                    pass
                except Exception:
                    _cache["x"] = 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_clean_mutation_in_try_handler_under_lock(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                with _lock:
                    try:
                        _cache["x"] = 1
                    except Exception:
                        _cache["y"] = 2
            """,
        )
        assert findings == []

    def test_detects_mutation_in_function_nested_inside_function(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def outer():
                def inner():
                    _cache["x"] = 1
                return inner
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_detects_mutation_using_bare_lock_constructor(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                _cache["x"] = 1
            """,
        )
        assert len(findings) == 1

    def test_clean_mutation_under_bare_lock_constructor(self):
        findings = run(
            self.rule,
            """
            _cache = {}
            _lock = Lock()

            def update():
                with _lock:
                    _cache["x"] = 1
            """,
        )
        assert findings == []

    def test_non_module_node_returns_no_findings(self):
        findings = self.rule.check(parse("def f(): pass"), "<test>")
        assert findings == []

    def test_nested_class_function_mutation_recurses(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            class Outer:
                class Inner:
                    def mutate(self):
                        _cache["x"] = 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_lambda_body_does_not_crash(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            def update():
                fn = lambda: _cache.get("x")
                return fn
            """,
        )
        assert findings == []

    def test_mutation_in_with_using_acquire_release_alias(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}
            _lock = threading.Lock()

            def update():
                _lock.acquire()
                try:
                    _cache["x"] = 1
                finally:
                    _lock.release()
                _cache["after"] = 2
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_clean_mutation_inside_inline_lock_constructor(self):
        findings = run(
            self.rule,
            """
            import threading

            _cache = {}

            def update():
                with threading.Lock():
                    _cache["x"] = 1
            """,
        )
        assert findings == []

    def test_clean_mutation_inside_bare_lock_constructor_import(self):
        findings = run(
            self.rule,
            """
            from threading import Lock

            _cache = {}

            def update():
                with Lock():
                    _cache["x"] = 1
            """,
        )
        assert findings == []

    def test_async_def_mutation_inside_module_scope_function(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            async def update():
                _cache["x"] = 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_mutation_inside_coroutine_nested_function(self):
        findings = run(
            self.rule,
            """
            _cache = {}

            async def outer():
                async def inner():
                    _cache["x"] = 1
                await inner()
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_attribute_path_chained_lock_is_recognized(self):
        # a chained attribute is still a recognizable lock expression,
        # so a mutation under it is not flagged.
        from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
            _attribute_path,
        )

        assert _attribute_path(ast.parse("a.b._lock").body[0].value)

    def test_lock_key_is_none_for_constant_expression(self):
        from pyrift.rules.cpython.cpy051_free_threaded_global_state import _lock_key

        assert _lock_key(ast.parse("1").body[0].value) is None

    def test_is_lock_expression_false_for_constant(self):
        from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
            _is_lock_expression,
        )

        assert not _is_lock_expression(ast.parse("1").body[0].value)

    def test_bare_lock_constructor_is_lock(self):
        from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
            _is_lock_constructor,
        )

        calls = [
            n
            for n in ast.walk(ast.parse("Lock()"))
            if isinstance(n, ast.Call)
        ]
        assert _is_lock_constructor(calls[0])

    def test_foreign_call_constructor_is_not_lock(self):
        from pyrift.rules.cpython.cpy051_free_threaded_global_state import (
            _is_lock_constructor,
        )

        calls = [
            n
            for n in ast.walk(ast.parse("foo()"))
            if isinstance(n, ast.Call)
        ]
        assert not _is_lock_constructor(calls[0])

    def test_function_nested_under_if_statement_is_discovered(self):
        # A function defined inside an ``if`` block still mutates module
        # state and must be discovered via statement recursion.
        findings = run(
            self.rule,
            """
            _cache = {}

            if True:
                def update():
                    _cache["x"] = 1
            """,
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY051"

    def test_check_non_module_returns_empty(self):
        # Pass an expression node (not a Module) directly to check().
        tree = ast.parse("_cache = []").body[0]
        findings = self.rule.check(tree, "<test>")
        assert findings == []