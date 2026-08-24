import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy022_bool_inversion import BoolInversionRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY022:
    rule = BoolInversionRule()

    def test_detects_invert_true(self):
        findings = run(self.rule, "x = ~True")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY022"
        assert findings[0].severity == Severity.WARNING

    def test_detects_invert_false(self):
        findings = run(self.rule, "x = ~False")
        assert len(findings) == 1

    def test_clean_not_operator(self):
        findings = run(self.rule, "x = not True")
        assert len(findings) == 0

    def test_suggestion_mentions_not(self):
        findings = run(self.rule, "~True")
        assert "not" in findings[0].suggestion.lower()