import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy045_nan_hash import NanHashRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY045:
    rule = NanHashRule()

    def test_detects_hash_nan(self):
        findings = run(self.rule, "h = hash(float('nan'))")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY045"
        assert findings[0].severity == Severity.WARNING

    def test_detects_hash_nan_uppercase(self):
        findings = run(self.rule, "h = hash(float('NaN'))")
        assert len(findings) == 1

    def test_clean_hash_number(self):
        findings = run(self.rule, "h = hash(42)")
        assert len(findings) == 0

    def test_suggestion_mentions_isnan(self):
        findings = run(self.rule, "hash(float('nan'))")
        assert "isnan" in findings[0].suggestion.lower()