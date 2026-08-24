import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy032_reveal_type import RevealTypeRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY032:
    rule = RevealTypeRule()

    def test_detects_reveal_type_import(self):
        findings = run(self.rule, "from typing import reveal_type")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY032"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import cast")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import reveal_type")
        assert "typing_extensions" in findings[0].suggestion.lower()