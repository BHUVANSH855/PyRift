import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy024_typeguard import TypeGuardRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY024:
    rule = TypeGuardRule()

    def test_detects_typeguard_import(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY024"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import TypeGuard")
        assert "typing_extensions" in findings[0].suggestion.lower()