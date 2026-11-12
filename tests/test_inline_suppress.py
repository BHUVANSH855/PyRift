"""Tests for inline ``# pyrift: ignore[...]`` suppression."""
from __future__ import annotations

from pyrift.finding import Finding, Runtime, Severity
from pyrift.scanner import (
    _apply_inline_suppressions,
    _parse_inline_ignores,
    scan_source,
)

# ---------------------------------------------------------------------------
# Unit tests for _parse_inline_ignores
# ---------------------------------------------------------------------------


def test_parse_no_comment():
    src = "x = 1\ny = 2\n"
    assert _parse_inline_ignores(src) == {}


def test_parse_bare_ignore():
    src = "x = 1  # pyrift: ignore\n"
    result = _parse_inline_ignores(src)
    assert result == {1: None}


def test_parse_single_rule():
    src = "x = 1  # pyrift: ignore[CPY033]\n"
    result = _parse_inline_ignores(src)
    assert result == {1: {"CPY033"}}


def test_parse_multiple_rules():
    src = "x = 1  # pyrift: ignore[CPY033, PPY001]\n"
    result = _parse_inline_ignores(src)
    assert result == {1: {"CPY033", "PPY001"}}


def test_parse_case_insensitive():
    src = "x = 1  # PYRIFT: IGNORE[cpy033]\n"
    result = _parse_inline_ignores(src)
    assert result == {1: {"CPY033"}}


def test_parse_multiple_lines():
    src = (
        "a = 1\n"
        "b = 2  # pyrift: ignore[CPY001]\n"
        "c = 3\n"
        "d = 4  # pyrift: ignore\n"
    )
    result = _parse_inline_ignores(src)
    assert result == {2: {"CPY001"}, 4: None}


# ---------------------------------------------------------------------------
# Unit tests for _apply_inline_suppressions
# ---------------------------------------------------------------------------

def _make_finding(line: int, rule_id: str) -> Finding:
    return Finding(
        file="test.py",
        line=line,
        col=0,
        rule_id=rule_id,
        title="t",
        description="d",
        severity=Severity.WARNING,
        runtime=Runtime.CPYTHON,
    )


def test_apply_suppresses_matching_rule():
    src = "x = 1  # pyrift: ignore[CPY033]\n"
    findings = [_make_finding(1, "CPY033")]
    kept, count = _apply_inline_suppressions(findings, src)
    assert kept == []
    assert count == 1


def test_apply_keeps_non_matching_rule():
    src = "x = 1  # pyrift: ignore[CPY033]\n"
    findings = [_make_finding(1, "CPY001")]
    kept, count = _apply_inline_suppressions(findings, src)
    assert len(kept) == 1
    assert count == 0


def test_apply_bare_suppresses_all():
    src = "x = 1  # pyrift: ignore\n"
    findings = [_make_finding(1, "CPY033"), _make_finding(1, "CPY001")]
    kept, count = _apply_inline_suppressions(findings, src)
    assert kept == []
    assert count == 2


def test_apply_different_lines():
    src = "a = 1  # pyrift: ignore[CPY033]\nb = 2\n"
    findings = [_make_finding(1, "CPY033"), _make_finding(2, "CPY033")]
    kept, count = _apply_inline_suppressions(findings, src)
    assert len(kept) == 1
    assert kept[0].line == 2
    assert count == 1


def test_apply_no_comment_keeps_all():
    src = "x = 1\n"
    findings = [_make_finding(1, "CPY033")]
    kept, count = _apply_inline_suppressions(findings, src)
    assert len(kept) == 1
    assert count == 0


# ---------------------------------------------------------------------------
# Integration test: scan_source respects inline ignore
# ---------------------------------------------------------------------------

def test_scan_source_inline_ignore_suppresses(tmp_path):
    """A real rule finding is suppressed when the line has # pyrift: ignore."""
    # CPY002 triggers on e.add_note(...)
    source_suppressed = "e.add_note('x')  # pyrift: ignore[CPY002]\n"
    source_normal = "e.add_note('x')\n"

    findings_normal = scan_source(source_normal, filename="test.py")
    findings_suppressed = scan_source(source_suppressed, filename="test.py")

    # Normal scan must have at least one finding
    assert len(findings_normal) >= 1
    # Suppressed scan must have fewer (ideally zero CPY002 findings)
    cpy002_suppressed = [f for f in findings_suppressed if f.rule_id == "CPY002"]
    assert len(cpy002_suppressed) == 0


def test_scan_source_inline_ignore_bare_suppresses_all(tmp_path):
    """Bare # pyrift: ignore suppresses all findings on the line."""
    source = "e.add_note('x')  # pyrift: ignore\n"
    findings = scan_source(source, filename="test.py")
    # No findings should reference line 1
    line1_findings = [f for f in findings if f.line == 1]
    assert line1_findings == []


def test_scan_source_wrong_rule_does_not_suppress():
    """A wrong rule ID in the ignore comment does not suppress other rules."""
    source = "e.add_note('x')  # pyrift: ignore[CPY001]\n"
    findings = scan_source(source, filename="test.py")
    cpy002_findings = [f for f in findings if f.rule_id == "CPY002"]
    assert len(cpy002_findings) >= 1