import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy031_assert_never import AssertNeverRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY031:
    rule = AssertNeverRule()

    def test_detects_assert_never_import(self):
        findings = run(self.rule, "from typing import assert_never")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY031"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import assert_type")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import assert_never")
        assert "typing_extensions" in findings[0].suggestion.lower()