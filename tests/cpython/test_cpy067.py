"""Tests for CPY067 -- typing.NamedTuple keyword syntax deprecated 3.13, removed 3.15."""
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

    # --- True positives ---

    def test_detects_keyword_syntax(self):
        # Keyword form is what's removed in 3.15
        findings = run(self.rule, "NamedTuple('Point', x=int, y=int)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY067"
        assert findings[0].severity == Severity.ERROR

    def test_detects_typing_namedtuple_keyword(self):
        findings = run(self.rule, "typing.NamedTuple('Point', x=int)")
        assert len(findings) == 1

    def test_detects_typing_extensions_namedtuple_keyword(self):
        # typing_extensions >= 4.7.0 mirrors the same deprecation
        findings = run(self.rule, "typing_extensions.NamedTuple('Point', x=int)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY067"

    def test_single_keyword_field(self):
        findings = run(self.rule, "NamedTuple('Solo', value=str)")
        assert len(findings) == 1

    def test_many_keyword_fields(self):
        findings = run(self.rule, "NamedTuple('T', a=int, b=str, c=float)")
        assert len(findings) == 1

    # --- True negatives ---

    def test_clean_list_syntax(self):
        # List form is still valid
        findings = run(self.rule, "NamedTuple('Point', [('x', int), ('y', int)])")
        assert len(findings) == 0

    def test_clean_dict_syntax(self):
        # 2-arg dict form is not deprecated
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

    def test_does_not_flag_kwargs_unpacking(self):
        # **kwargs spread is not the keyword-field form
        findings = run(self.rule, "NamedTuple('Point', **fields)")
        assert len(findings) == 0

    def test_unrelated_function_named_namedtuple_not_flagged(self):
        # Only typing/typing_extensions or bare NamedTuple is in scope
        src = "mylib.NamedTuple('Point', x=int)"
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_empty_namedtuple_no_fields_no_flag(self):
        # NamedTuple("NT") with no fields and no keywords — not keyword form
        findings = run(self.rule, "NamedTuple('NT')")
        assert len(findings) == 0

    def test_empty_file(self):
        assert run(self.rule, "") == []

    # --- Metadata assertions ---

    def test_affected_from_is_3_13(self):
        # Deprecated in 3.13, not only on 3.15+
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert len(findings) == 1
        assert findings[0].affected_from == "3.13"

    def test_affected_until_is_empty(self):
        # Removal rule — fires forever from 3.13 (no upper bound)
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert findings[0].affected_until == ""

    def test_severity_is_error(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert findings[0].severity == Severity.ERROR

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert "3.13" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert "3.15" in findings[0].description

    def test_suggestion_mentions_class(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert len(findings) == 1
        assert "class" in findings[0].suggestion.lower()

    def test_suggestion_mentions_functional_syntax(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        # List-of-tuples functional form should be shown
        assert "[(" in findings[0].suggestion or "functional" in findings[0].suggestion.lower()

    def test_docs_url_points_to_3_15_removed(self):
        findings = run(self.rule, "NamedTuple('Point', x=int)")
        assert "3.15" in findings[0].docs_url
        assert "removed" in findings[0].docs_url