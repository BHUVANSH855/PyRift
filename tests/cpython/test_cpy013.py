import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy013_override import OverrideRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY013:
    rule = OverrideRule()

    def test_detects_override_import(self):
        findings = run(self.rule, "from typing import override")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY013"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import final")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import override")
        assert "typing_extensions" in findings[0].suggestion.lower()