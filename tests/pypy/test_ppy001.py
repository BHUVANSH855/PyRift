import ast
import textwrap

from pyrift.finding import Runtime, Severity
from pyrift.rules.pypy.ppy001_gc_finalizer import GcFinalizerRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: GcFinalizerRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY001:
    rule = GcFinalizerRule()

    def test_detects_close_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.file.close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"
        assert findings[0].runtime == Runtime.PYPY
        assert findings[0].severity == Severity.ERROR

    def test_detects_flush_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.conn.flush()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"

    def test_detects_release_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.lock.release()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_disconnect_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.connection.disconnect()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_cleanup_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.cleanup()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_shutdown_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.service.shutdown()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_terminate_in_del(self):
        src = """
        class MyResource:
            def __del__(self):
                self.process.terminate()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_bare_function_resource_call(self):
        src = """
        class MyResource:
            def __del__(self):
                close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"

    def test_detects_multiple_resource_calls(self):
        src = """
        class MyResource:
            def __del__(self):
                self.file.flush()
                self.file.close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1
        assert "flush()" in findings[0].description
        assert "close()" in findings[0].description

    def test_clean_del_no_resource(self):
        src = """
        class MyResource:
            def __del__(self):
                self.count -= 1
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_normal_method_with_resource_cleanup(self):
        src = """
        class MyResource:
            def close(self):
                self.file.close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_function_named_del_but_not_method(self):
        src = """
        def not_a_finalizer():
            close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_detects_nested_cleanup_call(self):
        src = """
        class MyResource:
            def __del__(self):
                if self.file:
                    self.file.close()
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_detects_cleanup_inside_try(self):
        src = """
        class MyResource:
            def __del__(self):
                try:
                    self.file.close()
                except Exception:
                    pass
        """

        findings = run(self.rule, src)

        assert len(findings) == 1

    def test_does_not_flag_unrelated_method_names(self):
        src = """
        class MyResource:
            def __del__(self):
                self.close_connection_later()
                self.cleanup_state()
                self.shutdown_flag = True
        """

        findings = run(self.rule, src)

        assert len(findings) == 0