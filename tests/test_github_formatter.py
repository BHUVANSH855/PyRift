"""
Tests for pyrift.formatters.github — GitHub Actions annotation formatter.
"""
from __future__ import annotations

import pytest

from pyrift.finding import Confidence, Finding, IntentBasis, Severity
from pyrift.formatters import to_github_annotations  # exercises __init__
from pyrift.formatters.github import (
    _annotation_level,
    _escape,
    to_github_annotations as _direct,
)
from pyrift.scanner import ScanResult


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_finding(
    *,
    rule_id: str = "CPY001",
    title: str = "Test finding",
    description: str = "A test description",
    severity: Severity = Severity.WARNING,
    file: str = "test.py",
    line: int = 10,
    col: int = 5,
) -> Finding:
    return Finding(
        file=file,
        line=line,
        col=col,
        rule_id=rule_id,
        title=title,
        description=description,
        severity=severity,
        confidence=Confidence.HIGH,
        intent_basis=IntentBasis.DOCUMENTED,
    )


def _result(*findings: Finding) -> ScanResult:
    return ScanResult(findings=list(findings), files_scanned=1)


# ── _escape ──────────────────────────────────────────────────────────────────

class TestEscape:
    def test_percent(self):
        assert _escape("%") == "%25"

    def test_carriage_return(self):
        assert _escape("\r") == "%0D"

    def test_newline(self):
        assert _escape("\n") == "%0A"

    def test_colon(self):
        assert _escape(":") == "%3A"

    def test_comma(self):
        assert _escape(",") == "%2C"

    def test_no_special_chars(self):
        assert _escape("hello world") == "hello world"

    def test_multiple_special_chars(self):
        result = _escape("a%b:c,d\ne")
        assert "%" not in result.replace("%25", "").replace("%3A", "").replace("%2C", "").replace("%0A", "")


# ── _annotation_level ────────────────────────────────────────────────────────

class TestAnnotationLevel:
    def test_error(self):
        f = _make_finding(severity=Severity.ERROR)
        assert _annotation_level(f) == "error"

    def test_warning(self):
        f = _make_finding(severity=Severity.WARNING)
        assert _annotation_level(f) == "warning"

    def test_info_maps_to_notice(self):
        f = _make_finding(severity=Severity.INFO)
        assert _annotation_level(f) == "notice"


# ── to_github_annotations ────────────────────────────────────────────────────

class TestToGithubAnnotations:
    def test_empty_result_returns_empty_string(self):
        result = _result()
        assert to_github_annotations(result) == ""

    def test_warning_finding_produces_warning_line(self):
        f = _make_finding(severity=Severity.WARNING)
        output = to_github_annotations(_result(f))
        assert output.startswith("::warning ")

    def test_error_finding_produces_error_line(self):
        f = _make_finding(severity=Severity.ERROR)
        output = to_github_annotations(_result(f))
        assert output.startswith("::error ")

    def test_info_finding_produces_notice_line(self):
        f = _make_finding(severity=Severity.INFO)
        output = to_github_annotations(_result(f))
        assert output.startswith("::notice ")

    def test_output_contains_file_and_line(self):
        f = _make_finding(file="src/foo.py", line=42)
        output = to_github_annotations(_result(f))
        assert "file=src/foo.py" in output
        assert "line=42" in output

    def test_output_contains_col_when_set(self):
        f = _make_finding(col=7)
        output = to_github_annotations(_result(f))
        assert "col=7" in output

    def test_no_col_param_when_col_is_zero(self):
        f = _make_finding(col=0)
        output = to_github_annotations(_result(f))
        assert "col=" not in output

    def test_title_contains_rule_id(self):
        f = _make_finding(rule_id="CPY055", title="NotImplemented bool")
        output = to_github_annotations(_result(f))
        assert "CPY055" in output

    def test_message_uses_description(self):
        f = _make_finding(description="Use x instead of y")
        output = to_github_annotations(_result(f))
        assert "Use x instead of y" in output

    def test_multiple_findings_produce_multiple_lines(self):
        f1 = _make_finding(line=1)
        f2 = _make_finding(line=2)
        output = to_github_annotations(_result(f1, f2))
        lines = output.splitlines()
        assert len(lines) == 2

    def test_special_chars_in_file_path_are_escaped(self):
        f = _make_finding(file="path/with:colon.py")
        output = to_github_annotations(_result(f))
        # colon in file path should be escaped
        assert "%3A" in output

    def test_newline_in_message_is_escaped(self):
        f = _make_finding(description="line one\nline two")
        output = to_github_annotations(_result(f))
        assert "\n" not in output.split("::")[-1]

    def test_importable_via_package_init(self):
        # Exercises pyrift/formatters/__init__.py import path
        from pyrift.formatters import to_github_annotations as fn
        assert callable(fn)

    def test_direct_and_package_import_are_same(self):
        assert to_github_annotations is _direct
