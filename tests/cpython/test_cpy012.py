import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy012_literal_string import LiteralStringRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY012:
    rule = LiteralStringRule()

    def test_detects_literal_string_import(self):
        findings = run(self.rule, "from typing import LiteralString")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY012"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import Literal")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import LiteralString")
        assert "typing_extensions" in findings[0].suggestion.lower()