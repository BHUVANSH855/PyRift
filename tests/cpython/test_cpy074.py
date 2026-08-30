import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy074_co_lnotab_deprecated import CoLnotabDeprecatedRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY074:
    rule = CoLnotabDeprecatedRule()

    def test_detects_lnotab(self):
        findings = run(self.rule, "code_obj.__lnotab__")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY074"
        assert findings[0].severity == Severity.WARNING

    def test_clean_co_lines(self):
        findings = run(self.rule, "code_obj.co_lines()")
        assert len(findings) == 0

    def test_suggestion_mentions_co_lines(self):
        findings = run(self.rule, "code_obj.__lnotab__")
        assert "co_lines" in findings[0].suggestion
