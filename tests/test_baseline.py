import json

import pytest

from pyrift.baseline import (
    BASELINE_VERSION,
    BaselineError,
    create_baseline,
    filter_baseline_findings,
    load_baseline,
)
from pyrift.finding import Finding, Runtime, Severity


def make_finding(
    *,
    file="src/example.py",
    line=10,
    rule_id="PPY999",
):
    return Finding(
        file=file,
        line=line,
        col=4,
        rule_id=rule_id,
        title="Example finding",
        description="Example description",
        severity=Severity.WARNING,
        runtime=Runtime.PYPY,
        affected_from="3.10",
        affected_until="3.13",
        suggestion="Example suggestion",
        docs_url="https://example.com",
    )


class TestCreateBaseline:
    def test_creates_baseline_file(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        create_baseline(
            [make_finding()],
            path,
        )

        assert path.exists()

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        assert data["version"] == BASELINE_VERSION
        assert len(data["findings"]) == 1

    def test_baseline_is_sorted(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        findings = [
            make_finding(file="b.py"),
            make_finding(file="a.py"),
        ]

        create_baseline(findings, path)

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        assert data["findings"] == sorted(data["findings"])

    def test_duplicate_findings_are_stored_once(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        finding = make_finding()

        create_baseline(
            [finding, finding],
            path,
        )

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        assert len(data["findings"]) == 1


class TestLoadBaseline:
    def test_missing_baseline_returns_empty_set(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        assert load_baseline(path) == set()

    def test_loads_fingerprints(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        data = {
            "version": BASELINE_VERSION,
            "findings": ["abc", "def"],
        }

        path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )

        assert load_baseline(path) == {"abc", "def"}

    def test_rejects_invalid_json(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        path.write_text(
            "{invalid",
            encoding="utf-8",
        )

        with pytest.raises(BaselineError):
            load_baseline(path)

    def test_rejects_invalid_version(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        path.write_text(
            json.dumps(
                {
                    "version": 999,
                    "findings": [],
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(BaselineError):
            load_baseline(path)

    def test_rejects_non_list_findings(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        path.write_text(
            json.dumps(
                {
                    "version": BASELINE_VERSION,
                    "findings": {},
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(BaselineError):
            load_baseline(path)

    def test_rejects_non_string_fingerprints(self, tmp_path):
        path = tmp_path / ".pyrift-baseline.json"

        path.write_text(
            json.dumps(
                {
                    "version": BASELINE_VERSION,
                    "findings": ["abc", 123],
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(BaselineError):
            load_baseline(path)


class TestFilterBaselineFindings:
    def test_separates_baseline_and_new_findings(self):
        existing = make_finding(
            file="existing.py"
        )
        new = make_finding(
            file="new.py"
        )

        baseline_path = {
            __import__(
                "pyrift.fingerprint",
                fromlist=["finding_fingerprint"],
            ).finding_fingerprint(existing)
        }

        new_findings, baseline_findings = (
            filter_baseline_findings(
                [existing, new],
                baseline_path,
            )
        )

        assert new_findings == [new]
        assert baseline_findings == [existing]

    def test_empty_baseline_keeps_all_findings(self):
        findings = [
            make_finding(file="a.py"),
            make_finding(file="b.py"),
        ]

        new_findings, baseline_findings = (
            filter_baseline_findings(
                findings,
                set(),
            )
        )

        assert new_findings == findings
        assert baseline_findings == []

    def test_all_baselined_findings_are_filtered(self):
        findings = [
            make_finding(file="a.py"),
            make_finding(file="b.py"),
        ]

        from pyrift.fingerprint import finding_fingerprint

        baseline = {
            finding_fingerprint(finding)
            for finding in findings
        }

        new_findings, baseline_findings = (
            filter_baseline_findings(
                findings,
                baseline,
            )
        )

        assert new_findings == []
        assert baseline_findings == findings

class TestBaselineEdgeCases:
    def test_malformed_baseline_not_dict(self, tmp_path):
        """Baseline must be a JSON object, not an array."""
        import json

        from pyrift.baseline import BaselineError, load_baseline
        baseline_file = tmp_path / ".pyrift-baseline.json"
        baseline_file.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(BaselineError, match="JSON object"):
            load_baseline(baseline_file)