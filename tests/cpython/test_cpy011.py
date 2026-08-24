import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy011_typing_self import TypingSelfRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY011:
    rule = TypingSelfRule()

    def test_detects_self_import(self):
        findings = run(self.rule, "from typing import Self")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY011"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Optional")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import Self")
        assert "typing_extensions" in findings[0].suggestion.lower()