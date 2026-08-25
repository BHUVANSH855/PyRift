import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy034_hash_minus_one import HashMinusOneRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY034:
    rule = HashMinusOneRule()

    def test_detects_hash_stored(self):
        findings = run(self.rule, "h = hash(obj)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY034"
        assert findings[0].severity == Severity.INFO

    def test_detects_hash_compared(self):
        findings = run(self.rule, "if hash(x) == hash(y): pass")
        assert len(findings) >= 1

    def test_clean_hash_as_dict_key(self):
        # hash() used as dict key directly — not stored or compared
        findings = run(self.rule, "d = {hash(x): x for x in items}")
        assert len(findings) == 0

    def test_clean_hash_in_set(self):
        findings = run(self.rule, "s = {hash(x) for x in items}")
        assert len(findings) == 0

    def test_suggestion_mentions_persistent(self):
        findings = run(self.rule, "h = hash(obj)")
        assert "persist" in findings[0].suggestion.lower() or \
               "store" in findings[0].suggestion.lower()