import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
    TypingTypedDictFunctionalRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY077:
    rule = TypingTypedDictFunctionalRule()

    def test_detects_dict_form(self):
        code = "from typing import TypedDict\nPoint = TypedDict('Point', {'x': int, 'y': int})"
        findings = run(self.rule, code)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"
        assert findings[0].severity == Severity.WARNING

    def test_detects_keyword_form(self):
        code = "from typing import TypedDict\nPoint = TypedDict('Point', x=int, y=int)"
        findings = run(self.rule, code)
        assert len(findings) == 1

    def test_clean_class_syntax(self):
        code = "from typing import TypedDict\nclass Point(TypedDict):\n    x: int"
        findings = run(self.rule, code)
        assert len(findings) == 0

    def test_suggestion_mentions_class(self):
        code = "from typing import TypedDict\nPoint = TypedDict('Point', {'x': int})"
        findings = run(self.rule, code)
        assert "class" in findings[0].suggestion.lower()
