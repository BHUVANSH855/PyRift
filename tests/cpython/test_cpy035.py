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