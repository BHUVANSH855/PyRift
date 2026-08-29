import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy035_removeprefix import RemovePrefixRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY035:
    rule = RemovePrefixRule()

    def test_detects_removeprefix(self):
        findings = run(self.rule, "s = 'hello world'\ns.removeprefix('hello ')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY035"
        assert findings[0].severity == Severity.ERROR

    def test_detects_removesuffix(self):
        findings = run(self.rule, "s.removesuffix('.txt')")
        assert len(findings) == 1

    def test_clean_other_str_method(self):
        findings = run(self.rule, "s.strip()")
        assert len(findings) == 0

    def test_suggestion_mentions_startswith(self):
        findings = run(self.rule, "s.removeprefix('x')")
        assert "startswith" in findings[0].suggestion.lower()

    def test_clean_try_except_attribute_error(self):
        # Inside try/except AttributeError — already guarded
        findings = run(self.rule, """\
            try:
                s.removeprefix('hello ')
            except AttributeError:
                pass
        """)
        assert len(findings) == 0

    def test_clean_version_guard(self):
        # Inside sys.version_info >= (3, 9) — already guarded
        findings = run(self.rule, """\
            import sys
            if sys.version_info >= (3, 9):
                s.removeprefix('hello ')
        """)
        assert len(findings) == 0

    def test_clean_try_except_removesuffix(self):
        # removesuffix in try/except is also guarded
        findings = run(self.rule, """\
            try:
                s.removesuffix('.txt')
            except AttributeError:
                pass
        """)
        assert len(findings) == 0

    def test_still_flags_unguarded(self):
        # Unguarded call should still be flagged
        findings = run(self.rule, "s.removeprefix('x')")
        assert len(findings) == 1

    def test_clean_try_except_bare(self):
        # Bare except also guards
        findings = run(self.rule, """\
            try:
                s.removeprefix('x')
            except:
                pass
        """)
        assert len(findings) == 0