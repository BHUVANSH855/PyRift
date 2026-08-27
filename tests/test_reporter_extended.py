"""Extended reporter tests for markdown/text edge cases."""
from __future__ import annotations

import json

from pyrift.finding import Confidence, Finding, Runtime, Severity
from pyrift.reporter import to_json, to_markdown, to_text
from pyrift.scanner import ScanResult


def make_result(
    findings=None,
    files_scanned=5,
    rule_errors=None,
    baseline_suppressed=0,
):
    return ScanResult(
        findings=findings or [],
        files_scanned=files_scanned,
        rule_errors=rule_errors or [],
        baseline_suppressed=baseline_suppressed,
    )


def make_finding(rule_id="CPY001", severity=Severity.WARNING):
    return Finding(
        file="test.py", line=10, col=0,
        rule_id=rule_id, title="Test finding",
        description="Test description",
        severity=severity,
        confidence=Confidence.HIGH,
        runtime=Runtime.CPYTHON,
        affected_from="3.10", affected_until="3.13",
        suggestion="Fix it.",
        docs_url="https://example.com",
    )


class TestToMarkdown:
    def test_no_findings_clean(self):
        result = make_result()
        md = to_markdown(result)
        assert "OK" in md or "No behaviour" in md

    def test_no_findings_with_rule_errors(self):
        result = make_result(rule_errors=["CPY001: error"])
        md = to_markdown(result)
        assert "WARN" in md or "rule" in md.lower() or "error" in md.lower()

    def test_no_findings_with_baseline_suppressed(self):
        result = make_result(baseline_suppressed=3)
        md = to_markdown(result)
        assert "3" in md

    def test_with_findings(self):
        result = make_result(findings=[make_finding()])
        md = to_markdown(result)
        assert "CPY001" in md
        assert "Test finding" in md

    def test_with_error_severity(self):
        result = make_result(findings=[make_finding(severity=Severity.ERROR)])
        md = to_markdown(result)
        assert "error" in md.lower() or "ERROR" in md

    def test_summary_contains_file_count(self):
        result = make_result(files_scanned=42)
        md = to_markdown(result)
        assert "42" in md


class TestToText:
    def test_no_findings(self):
        result = make_result()
        text = to_text(result)
        assert text  # at minimum no crash

    def test_no_findings_with_rule_errors(self):
        result = make_result(rule_errors=["CPY001: error"])
        text = to_text(result)
        assert text

    def test_with_findings(self):
        result = make_result(findings=[make_finding()])
        text = to_text(result)
        assert "CPY001" in text

    def test_baseline_suppressed_shown(self):
        result = make_result(baseline_suppressed=5)
        text = to_text(result)
        assert "5" in text or "baseline" in text.lower()


class TestToJson:
    def test_json_structure(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_json(result))
        assert "summary" in data
        assert "findings" in data
        assert data["summary"]["total_findings"] == 1

    def test_json_confidence_field(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_json(result))
        assert "confidence" in data["findings"][0]
        assert data["findings"][0]["confidence"] == "high"

    def test_json_no_findings(self):
        result = make_result()
        data = json.loads(to_json(result))
        assert data["summary"]["total_findings"] == 0
        assert data["findings"] == []

    def test_json_severity_counts(self):
        findings = [
            make_finding(severity=Severity.ERROR),
            make_finding(severity=Severity.WARNING),
            make_finding(severity=Severity.INFO),
        ]
        result = make_result(findings=findings)
        data = json.loads(to_json(result))
        assert data["summary"]["errors"] == 1
        assert data["summary"]["warnings"] == 1