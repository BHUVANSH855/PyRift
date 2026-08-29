import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy034_bit_count import BitCountRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY034:
    rule = BitCountRule()

    def test_detects_bit_count(self):
        findings = run(self.rule, "n = 42\nc = n.bit_count()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY034"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_int_method(self):
        findings = run(self.rule, "n.bit_length()")
        assert len(findings) == 0

    def test_suggestion_mentions_bin(self):
        findings = run(self.rule, "n.bit_count()")
        assert "bin" in findings[0].suggestion.lower()

    def test_clean_try_except_attribute_error(self):
        # Inside try/except AttributeError — already guarded
        findings = run(self.rule, """\
            try:
                n.bit_count()
            except AttributeError:
                pass
        """)
        assert len(findings) == 0

    def test_clean_version_guard(self):
        # Inside sys.version_info >= (3, 10) — already guarded
        findings = run(self.rule, """\
            import sys
            if sys.version_info >= (3, 10):
                n.bit_count()
        """)
        assert len(findings) == 0

    def test_still_flags_unguarded(self):
        # Unguarded call should still be flagged
        findings = run(self.rule, "n.bit_count()")
        assert len(findings) == 1

    def test_clean_try_except_bare(self):
        # Bare except also guards
        findings = run(self.rule, """\
            try:
                n.bit_count()
            except:
                pass
        """)
        assert len(findings) == 0