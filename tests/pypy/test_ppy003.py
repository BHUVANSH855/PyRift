import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy003_getrefcount import GetRefcountRule


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))


def run(rule: GetRefcountRule, src: str):
    return rule.check(parse(src), "<test>")


class TestPPY003:
    rule = GetRefcountRule()

    def test_detects_getrefcount(self):
        findings = run(
            self.rule,
            "import sys\nx = sys.getrefcount(obj)",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY003"
        assert findings[0].severity == Severity.ERROR

    def test_detects_multiple_getrefcount_calls(self):
        findings = run(
            self.rule,
            """
            import sys

            first = sys.getrefcount(obj)
            second = sys.getrefcount(other)
            """,
        )

        assert len(findings) == 2

    def test_detects_getrefcount_in_function(self):
        findings = run(
            self.rule,
            """
            import sys

            def check_refs(obj):
                return sys.getrefcount(obj)
            """,
        )

        assert len(findings) == 1

    def test_clean_sys_version(self):
        findings = run(
            self.rule,
            "import sys\nprint(sys.version)",
        )

        assert len(findings) == 0

    def test_clean_other_sys_function(self):
        findings = run(
            self.rule,
            "import sys\nsys.getsizeof(obj)",
        )

        assert len(findings) == 0

    def test_clean_unrelated_getrefcount(self):
        findings = run(
            self.rule,
            "obj.getrefcount()",
        )

        assert len(findings) == 0

    def test_clean_unrelated_module(self):
        findings = run(
            self.rule,
            "other.getrefcount(obj)",
        )

        assert len(findings) == 0

    def test_suggestion_mentions_gc(self):
        findings = run(
            self.rule,
            "sys.getrefcount(x)",
        )

        assert "gc" in findings[0].suggestion.lower()