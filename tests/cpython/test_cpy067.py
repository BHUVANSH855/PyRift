import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy067_typing_namedtuple_keyword import (
    TypingNamedTupleKeywordRule,
)


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY067:
    rule = TypingNamedTupleKeywordRule()

    def test_detects_keyword_syntax(self):
        # Keyword form is what's removed in 3.15
        findings = run(self.rule, "NamedTuple('Point', x=int, y=int)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY067"
        assert findings[0].severity == Severity.ERROR

    def test_detects_typing_namedtuple_keyword(self):
        findings = run(self.rule, "typing.NamedTuple('Point', x=int)")
        assert len(findings) == 1

    def test_clean_list_syntax(self):
        # List form is still valid
        findings = run(self.rule, "NamedTuple('Point', [('x', int), ('y', int)])")
        assert len(findings) == 0

    def test_clean_dict_syntax(self):
        # Dict form is still valid
        findings = run(self.rule, "NamedTuple('Point', {'x': int})")
        assert len(findings) == 0

    def test_clean_class_syntax(self):
        src = """
class Point(NamedTuple):
    x: int
    y: int
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_suggestion_mentions_class(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert len(findings) == 1
        assert "class" in findings[0].suggestion.lower()