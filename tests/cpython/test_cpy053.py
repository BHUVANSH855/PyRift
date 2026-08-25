import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy053_typing_get_overloads import TypingGetOverloadsRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY053:
    rule = TypingGetOverloadsRule()

    def test_detects_import(self):
        findings = run(self.rule, "from typing import get_overloads")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY053"
        assert findings[0].severity == Severity.ERROR

    def test_detects_attribute_call(self):
        findings = run(self.rule, "import typing\ntyping.get_overloads(fn)")
        assert len(findings) == 1

    def test_clean_other_typing_import(self):
        findings = run(self.rule, "from typing import overload")
        assert len(findings) == 0

    def test_suggestion_mentions_typing_extensions(self):
        findings = run(self.rule, "from typing import get_overloads")
        assert "typing_extensions" in findings[0].suggestion.lower()