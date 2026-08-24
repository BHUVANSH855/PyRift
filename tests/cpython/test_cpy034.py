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