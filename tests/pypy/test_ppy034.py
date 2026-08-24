import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy034_hash_minus_one import HashMinusOneRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY034:
    rule = HashMinusOneRule()

    def test_detects_hash_call(self):
        findings = run(self.rule, "h = hash(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY034"
        assert findings[0].severity == Severity.INFO

    def test_detects_hash_minus_one(self):
        findings = run(self.rule, "h = hash(-1)")
        assert len(findings) == 1

    def test_suggestion_mentions_persistent(self):
        findings = run(self.rule, "hash(x)")
        assert "persist" in findings[0].suggestion.lower() or \
               "store" in findings[0].suggestion.lower()