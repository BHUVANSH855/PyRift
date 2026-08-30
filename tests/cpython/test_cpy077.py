import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy077_typing_typeddict_functional import (
    TypingTypedDictFunctionalRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY077:
    rule = TypingTypedDictFunctionalRule()

    def test_detects_zero_field_form(self):
        # Zero-field form removed in 3.15
        findings = run(self.rule, "TypedDict('Name')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"
        assert findings[0].severity == Severity.ERROR

    def test_detects_none_field_form(self):
        # None-field form removed in 3.15
        findings = run(self.rule, "TypedDict('Name', None)")
        assert len(findings) == 1

    def test_clean_dict_form(self):
        # Dict form is still valid per Python 3.15 docs
        findings = run(self.rule, "TypedDict('Point', {'x': int, 'y': int})")
        assert len(findings) == 0

    def test_clean_class_syntax(self):
        src = """
class Point(TypedDict):
    x: int
    y: int
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_class(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert len(findings) == 1
        assert "class" in findings[0].suggestion.lower()