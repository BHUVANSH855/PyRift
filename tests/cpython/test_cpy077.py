"""Tests for CPY077 — typing.TypedDict zero/None-field syntax deprecated 3.13, removed 3.15."""
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

    # ------------------------------------------------------------------ #
    # Detection                                                            #
    # ------------------------------------------------------------------ #

    def test_detects_zero_field_bare_name(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"
        assert findings[0].severity == Severity.ERROR

    def test_detects_zero_field_qualified(self):
        findings = run(self.rule, "typing.TypedDict('Name')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"

    def test_detects_none_field_bare_name(self):
        findings = run(self.rule, "TypedDict('Name', None)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"

    def test_detects_none_field_qualified(self):
        findings = run(self.rule, "typing.TypedDict('Name', None)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY077"

    def test_detects_zero_field_assigned(self):
        findings = run(self.rule, "TD = TypedDict('TD')")
        assert len(findings) == 1

    def test_detects_none_field_assigned(self):
        findings = run(self.rule, "TD = TypedDict('TD', None)")
        assert len(findings) == 1

    # ------------------------------------------------------------------ #
    # Negative cases — forms that are still valid                         #
    # ------------------------------------------------------------------ #

    def test_clean_dict_form_with_fields(self):
        findings = run(self.rule, "TypedDict('Point', {'x': int, 'y': int})")
        assert len(findings) == 0

    def test_clean_dict_form_empty_dict(self):
        """TypedDict("TD", {}) is the correct zero-field functional form."""
        findings = run(self.rule, "TypedDict('TD', {})")
        assert len(findings) == 0

    def test_clean_class_syntax(self):
        src = textwrap.dedent("""\
            class Point(TypedDict):
                x: int
                y: int
        """)
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_class_syntax_zero_field(self):
        src = textwrap.dedent("""\
            class Empty(TypedDict):
                pass
        """)
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_keyword_arg_form_not_double_flagged(self):
        """TypedDict("TD", x=int) is the kw-arg form, removed in 3.13.
        CPY077 must NOT also fire on it — it has zero positional args
        after the name, but n.keywords is non-empty, so the guard fires."""
        findings = run(self.rule, "TypedDict('TD', x=int)")
        assert len(findings) == 0

    def test_clean_unrelated_call_named_typeddict_with_dict(self):
        findings = run(self.rule, "TypedDict('Point', {'x': int})")
        assert len(findings) == 0

    def test_clean_non_typeddict_zero_arg_call(self):
        findings = run(self.rule, "SomeOtherClass('Name')")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------ #
    # Suggestion / description / metadata                                  #
    # ------------------------------------------------------------------ #

    def test_suggestion_mentions_class_syntax(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert "class" in findings[0].suggestion.lower()

    def test_suggestion_mentions_empty_dict_form(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert "{}" in findings[0].suggestion

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert "3.13" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert "3.15" in findings[0].description

    def test_severity_is_error(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert findings[0].severity == Severity.ERROR

    def test_affected_from_is_3_13(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert findings[0].affected_from == "3.13"

    def test_affected_until_is_empty(self):
        """Removed in 3.15 — no upper bound (fires forever from 3.13 onward)."""
        findings = run(self.rule, "TypedDict('Name')")
        assert findings[0].affected_until == ""

    def test_docs_url_points_to_3_15_removed(self):
        findings = run(self.rule, "TypedDict('Name')")
        assert "3.15" in findings[0].docs_url
        assert "removed" in findings[0].docs_url