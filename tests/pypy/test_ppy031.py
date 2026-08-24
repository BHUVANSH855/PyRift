import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy031_integer_identity import IntegerIdentityRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY031:
    rule = IntegerIdentityRule()

    def test_detects_is_comparison(self):
        findings = run(self.rule, "if x is y: pass")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY031"
        assert findings[0].severity == Severity.INFO

    def test_detects_is_not_comparison(self):
        findings = run(self.rule, "if x is not y: pass")
        assert len(findings) == 1

    def test_suggestion_mentions_equality(self):
        findings = run(self.rule, "x is y")
        assert "==" in findings[0].suggestion

    def test_docs_url_present(self):
        findings = run(self.rule, "x is y")
        assert findings[0].docs_url != ""