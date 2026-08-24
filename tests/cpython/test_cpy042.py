import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy042_aiter_anext import AiterAnextRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY042:
    rule = AiterAnextRule()

    def test_detects_aiter(self):
        findings = run(self.rule, "it = aiter(async_gen)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY042"
        assert findings[0].severity == Severity.ERROR

    def test_detects_anext(self):
        findings = run(self.rule, "val = anext(it)")
        assert len(findings) == 1

    def test_clean_regular_iter(self):
        findings = run(self.rule, "it = iter(lst)")
        assert len(findings) == 0

    def test_suggestion_mentions_version(self):
        findings = run(self.rule, "aiter(x)")
        assert "3, 10" in findings[0].suggestion or "3.10" in findings[0].suggestion