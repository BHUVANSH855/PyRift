import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy074_co_lnotab_deprecated import CoLnotabDeprecatedRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY074:
    rule = CoLnotabDeprecatedRule()

    # --- detection ---

    def test_detects_co_lnotab(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY074"
        assert findings[0].severity == Severity.ERROR

    def test_detects_co_lnotab_on_func_code(self):
        findings = run(self.rule, "func.__code__.co_lnotab")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY074"

    def test_detects_co_lnotab_via_code_module(self):
        # 'code' as a variable name is a common convention
        findings = run(self.rule, "code.co_lnotab")
        assert len(findings) == 1

    def test_detects_co_lnotab_in_expression(self):
        findings = run(self.rule, "print(obj.co_lnotab)")
        assert len(findings) == 1

    def test_detects_co_lnotab_assigned(self):
        findings = run(self.rule, "tab = code_obj.co_lnotab")
        assert len(findings) == 1

    def test_detects_multiple_co_lnotab_accesses(self):
        src = "a = x.co_lnotab\nb = y.co_lnotab"
        findings = run(self.rule, src)
        assert len(findings) == 2

    # --- negative cases ---

    def test_clean_co_lines(self):
        """co_lines() is the correct replacement — must NOT fire."""
        findings = run(self.rule, "code_obj.co_lines()")
        assert len(findings) == 0

    def test_clean_co_linetable(self):
        findings = run(self.rule, "code_obj.co_linetable")
        assert len(findings) == 0

    def test_clean_co_positions(self):
        findings = run(self.rule, "code_obj.co_positions()")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "obj.lnotab")
        assert len(findings) == 0

    def test_old_wrong_name_does_not_fire(self):
        """__lnotab__ (with dunders) is NOT the real attribute name — must not fire."""
        findings = run(self.rule, "code_obj.__lnotab__")
        assert len(findings) == 0

    def test_clean_no_attribute_access(self):
        findings = run(self.rule, "x = 1 + 2")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # --- finding content ---

    def test_suggestion_mentions_co_lines(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "co_lines" in findings[0].suggestion

    def test_description_mentions_deprecated(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "deprecated" in findings[0].description.lower()

    def test_description_mentions_pep_626(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "626" in findings[0].description

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "3.10" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "3.15" in findings[0].description

    def test_docs_url_points_to_pep_626_or_whatsnew(self):
        findings = run(self.rule, "code_obj.co_lnotab")
        assert "3.10" in findings[0].docs_url or "3.15" in findings[0].docs_url

    def test_severity_is_error(self):
        """Removed in 3.15 — severity is ERROR, not WARNING."""
        findings = run(self.rule, "code_obj.co_lnotab")
        assert findings[0].severity == Severity.ERROR

    # --- metadata ---

    def test_affected_from_is_3_10(self):
        """PEP 626 deprecated co_lnotab in 3.10."""
        findings = run(self.rule, "code_obj.co_lnotab")
        assert findings[0].affected_from == "3.10"

    def test_affected_until_is_empty(self):
        """Removed in 3.15 — no upper bound (fires forever from 3.10 onward)."""
        findings = run(self.rule, "code_obj.co_lnotab")
        assert findings[0].affected_until == ""