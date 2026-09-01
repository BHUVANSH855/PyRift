import ast
import textwrap

from pyrift.rules.pypy.ppy008_threading_local import ThreadingLocalRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: ThreadingLocalRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY008:
    rule = ThreadingLocalRule()

    def test_detects_threading_local(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY008"

    def test_clean_other_threading_call(self):
        findings = run(
            self.rule,
            """
            import threading

            t = threading.Thread()
            """,
        )

        assert len(findings) == 0

    def test_explicit_attribute_cleanup_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()
            local.value = object()
            del local.value
            """,
        )

        assert len(findings) == 0

    def test_cleanup_in_finally_is_not_flagged(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()

            try:
                local.value = object()
            finally:
                del local.value
            """,
        )

        assert len(findings) == 0

    def test_multiple_local_attributes_with_cleanup(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()
            local.connection = object()
            local.buffer = object()

            del local.connection
            del local.buffer
            """,
        )

        assert len(findings) == 0

    def test_unrelated_delete_does_not_suppress_finding(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()
            other = object()

            del other
            """,
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY008"

    def test_suggestion_mentions_cleanup(self):
        findings = run(
            self.rule,
            """
            import threading

            local = threading.local()
            """,
        )

        assert (
            "del" in findings[0].suggestion.lower()
            or "clean" in findings[0].suggestion.lower()
        )