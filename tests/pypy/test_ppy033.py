import ast
import textwrap

from pyrift.rules.pypy.ppy033_del_ignored_exceptions import (
    DelIgnoredExceptionsRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestPPY033:
    rule = DelIgnoredExceptionsRule()

    def test_detects_del_with_calls(self):
        src = """
        class MyClass:
            def __del__(self):
                self.cleanup()
                self.close()
        """
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY033"

    def test_detects_del_with_raise(self):
        src = """
        class MyClass:
            def __del__(self):
                raise RuntimeError("cleanup failed")
        """
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY033"

    def test_clean_empty_del(self):
        src = """
        class MyClass:
            def __del__(self):
                pass
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_del_without_calls_or_raise(self):
        src = """
        class MyClass:
            def __del__(self):
                self.value = None
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_try_except(self):
        src = """
        class MyClass:
            def __del__(self):
                self.close()
        """
        findings = run(self.rule, src)
        assert "try" in findings[0].suggestion.lower() or \
            "except" in findings[0].suggestion.lower()

    def test_ignores_rgca_light_finalizer_decorator(self):
        src = """
        from rpython.rlib import rgc

        class MyClass:
            @rgc.must_be_light_finalizer
            def __del__(self):
                self.cleanup()
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_ignores_direct_light_finalizer_decorator(self):
        src = """
        class MyClass:
            @must_be_light_finalizer
            def __del__(self):
                self.cleanup()
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_known_cleanup_primitive_is_clean(self):
        src = """
        import lltype

        class MyClass:
            def __del__(self):
                lltype.free(self.ptr)
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_known_raw_cleanup_primitive_is_clean(self):
        src = """
        class MyClass:
            def __del__(self):
                free_raw_storage(self.storage)
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_raw_free_is_clean(self):
        src = """
        class MyClass:
            def __del__(self):
                llmemory.raw_free(self.addr)
        """
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_normal_decorator_still_detected(self):
        src = """
        def decorator(func):
            return func

        class MyClass:
            @decorator
            def __del__(self):
                self.cleanup()
        """
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY033"

    def test_close_call_is_still_detected(self):
        src = """
        class MyClass:
            def __del__(self):
                self.close()
        """
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY033"