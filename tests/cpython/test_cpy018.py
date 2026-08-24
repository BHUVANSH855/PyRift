import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy018_required import RequiredRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY018:
    rule = RequiredRule()

    def test_detects_required_import(self):
        findings = run(self.rule, "from typing import Required")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY018"
        assert findings[0].severity == Severity.ERROR

    def test_detects_not_required_import(self):
        findings = run(self.rule, "from typing import NotRequired")
        assert len(findings) == 1

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Required")
        assert "typing_extensions" in findings[0].suggestion.lower()