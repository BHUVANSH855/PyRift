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