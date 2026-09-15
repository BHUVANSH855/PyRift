import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy022_bool_inversion import BoolInversionRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY022:
    rule = BoolInversionRule()

    def test_detects_invert_true(self):
        findings = run(self.rule, "x = ~True")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY022"
        assert findings[0].severity == Severity.WARNING

    def test_detects_invert_false(self):
        findings = run(self.rule, "x = ~False")
        assert len(findings) == 1

    def test_detects_nested_bool_inversion(self):
        findings = run(self.rule, "x = ~(True)")
        assert len(findings) == 1

    def test_detects_bool_in_expression(self):
        findings = run(self.rule, "x = 1 + ~True")
        assert len(findings) == 1

    def test_clean_not_operator(self):
        findings = run(self.rule, "x = not True")
        assert findings == []

    def test_clean_integer_inversion(self):
        findings = run(self.rule, "x = ~1")
        assert findings == []

    def test_clean_negative_integer_inversion(self):
        findings = run(self.rule, "x = ~(-1)")
        assert findings == []

    def test_clean_variable_inversion(self):
        # Without type inference, do not assume that x is a bool.
        # It may legitimately be an integer or another object that
        # implements __invert__.
        findings = run(self.rule, "x = ~value")
        assert findings == []

    def test_clean_call_result_inversion(self):
        findings = run(self.rule, "x = ~get_value()")
        assert findings == []

    def test_clean_bitwise_inversion_of_integer_expression(self):
        findings = run(self.rule, "x = ~(1 << 4)")
        assert findings == []

    def test_suggestion_mentions_not(self):
        findings = run(self.rule, "x = ~True")
        assert "not" in findings[0].suggestion.lower()

    def test_suggestion_mentions_explicit_int_conversion(self):
        findings = run(self.rule, "x = ~True")
        assert "~int" in findings[0].suggestion.lower()

    def test_description_identifies_python_312_deprecation(self):
        findings = run(self.rule, "x = ~True")
        assert "Python 3.12" in findings[0].description
        assert "deprecated" in findings[0].description.lower()

    def test_description_identifies_python_316_removal(self):
        findings = run(self.rule, "x = ~True")
        assert "Python 3.16" in findings[0].description

    def test_affected_version_starts_at_python_312(self):
        findings = run(self.rule, "x = ~True")
        assert findings[0].affected_from == "3.12"

    def test_docs_url_points_to_python_312_whats_new(self):
        findings = run(self.rule, "x = ~True")
        assert findings[0].docs_url == "https://docs.python.org/3/whatsnew/3.12.html"
