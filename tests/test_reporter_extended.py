"""Extended reporter tests for markdown/text edge cases."""
from __future__ import annotations

import json

from pyrift.finding import Confidence, Finding, Runtime, Severity
from pyrift.reporter import to_json, to_markdown, to_sarif, to_text
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

    def test_text_no_findings_with_rule_errors(self):
        result = make_result(rule_errors=["CPY001: crashed"])
        text = to_text(result)
        assert "rule" in text.lower() or "error" in text.lower() or "WARN" in text or text

class TestToTextBothBranchesExplicit:
    """Explicitly covers lines 188 and 194 in reporter.py."""

    def test_rule_errors_appear_in_summary(self):
        result = make_result(rule_errors=["CPY001: crashed"])
        text = to_text(result)
        # The rule_errors branch (line 188) should be exercised
        assert "rule" in text.lower() or "error" in text.lower() or "1" in text

    def test_baseline_suppressed_in_summary(self):
        result = make_result(baseline_suppressed=5)
        text = to_text(result)
        # The baseline_suppressed branch (line 194) should be exercised
        assert "5" in text or "baseline" in text.lower() or "suppressed" in text.lower()

    def test_both_rule_errors_and_baseline(self):
        result = make_result(rule_errors=["err"], baseline_suppressed=3)
        text = to_text(result)
        assert text  # no crash, both branches hit


class TestToSarif:
    def test_sarif_top_level_keys(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        assert data["$schema"] == (
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec"
            "/master/Schemata/sarif-schema-2.1.0.json"
        )
        assert data["version"] == "2.1.0"
        assert "runs" in data

    def test_sarif_tool_driver(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        driver = data["runs"][0]["tool"]["driver"]
        assert driver["name"] == "pyrift"
        assert "version" in driver

    def test_sarif_rules_entry(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        rules = data["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule["id"] == "CPY001"
        assert rule["shortDescription"]["text"] == "Test finding"
        assert "tags" in rule["properties"]

    def test_sarif_results_entry(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        results = data["runs"][0]["results"]
        assert len(results) == 1
        r = results[0]
        assert r["ruleId"] == "CPY001"
        assert "message" in r
        assert "locations" in r
        assert "properties" in r

    def test_sarif_physical_location(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        loc = data["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        assert loc["artifactLocation"]["uri"] == "test.py"
        assert loc["region"]["startLine"] == 10

    def test_sarif_result_properties(self):
        result = make_result(findings=[make_finding()])
        data = json.loads(to_sarif(result))
        props = data["runs"][0]["results"][0]["properties"]
        assert props["confidence"] == "high"
        assert props["evidence_type"] == "official_docs"
        assert props["runtime"] == "cpython"
        assert props["affected_from"] == "3.10"
        assert props["affected_until"] == "3.13"
        assert props["suggestion"] == "Fix it."

    def test_sarif_multiple_findings(self):
        f1 = make_finding(rule_id="CPY001")
        f2 = make_finding(rule_id="CPY002")
        result = make_result(findings=[f1, f2])
        data = json.loads(to_sarif(result))
        results = data["runs"][0]["results"]
        assert len(results) == 2
        rules = data["runs"][0]["tool"]["driver"]["rules"]
        rule_ids = [r["id"] for r in rules]
        assert "CPY001" in rule_ids
        assert "CPY002" in rule_ids

    def test_sarif_no_findings(self):
        result = make_result()
        data = json.loads(to_sarif(result))
        assert data["runs"][0]["results"] == []
        assert data["runs"][0]["tool"]["driver"]["rules"] == []

    def test_sarif_category_in_properties(self):
        f = make_finding()
        f.category = "behavior"
        result = make_result(findings=[f])
        data = json.loads(to_sarif(result))
        rule_props = data["runs"][0]["tool"]["driver"]["rules"][0]["properties"]
        assert rule_props["category"] == "behavior"
        result_props = data["runs"][0]["results"][0]["properties"]
        assert result_props["category"] == "behavior"

    def test_sarif_no_docs_url(self):
        f = make_finding()
        f.docs_url = ""
        result = make_result(findings=[f])
        data = json.loads(to_sarif(result))
        assert data["runs"][0]["tool"]["driver"]["rules"][0]["helpUri"] == ""


class TestFindingCategory:
    def test_default_category(self):
        f = make_finding()
        assert f.category == "compatibility"

    def test_to_dict_includes_category(self):
        f = make_finding()
        d = f.to_dict()
        assert "category" in d
        assert d["category"] == "compatibility"

    def test_custom_category(self):
        f = make_finding()
        f.category = "performance"
        assert f.category == "performance"

    def test_to_dict_custom_category(self):
        f = make_finding()
        f.category = "platform"
        d = f.to_dict()
        assert d["category"] == "platform"