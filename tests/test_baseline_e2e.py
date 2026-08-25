import json
from pathlib import Path

import pytest

from pyrift.baseline import (
    DEFAULT_BASELINE_FILE,
    create_baseline,
    filter_baseline_findings,
    load_baseline,
)
from pyrift.scanner import ScanResult, scan


def test_real_scan_baseline_workflow(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()

    source = project / "example.py"
    source.write_text(
        """
        import asyncio

        loop = asyncio.get_event_loop()
        """,
        encoding="utf-8",
    )

    monkeypatch.chdir(project)

    # 1. Perform a real scan.
    initial_result = scan(project)

    assert initial_result.findings

    initial_fingerprints = {
        (
            finding.rule_id,
            finding.file,
            finding.line,
        )
        for finding in initial_result.findings
    }

    assert initial_fingerprints

    # 2. Create a real baseline from those findings.
    baseline_path = project / DEFAULT_BASELINE_FILE

    create_baseline(
        initial_result.findings,
        baseline_path,
    )

    assert baseline_path.exists()

    # 3. Load the baseline again from disk.
    baseline = load_baseline(baseline_path)

    assert baseline

    # 4. Run another real scan.
    second_result = scan(project)

    assert second_result.findings

    # 5. Existing findings should all be recognized by
    #    the baseline.
    new_findings, baseline_findings = filter_baseline_findings(
        second_result.findings,
        baseline,
    )

    assert not new_findings
    assert baseline_findings

    # 6. Verify that the baseline contains the expected
    #    finding fingerprints.
    data = json.loads(
        baseline_path.read_text(encoding="utf-8")
    )

    assert data["version"] == 1
    assert data["findings"]

    baseline_fingerprints = set(data["findings"])

    assert len(baseline_fingerprints) == len(
        baseline
    )


def test_real_scan_detects_new_finding_after_baseline(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    source = project / "example.py"
    source.write_text(
        """
        import asyncio

        loop = asyncio.get_event_loop()
        """,
        encoding="utf-8",
    )

    monkeypatch.chdir(project)

    # Create the initial baseline.
    initial_result = scan(project)

    assert initial_result.findings

    baseline_path = project / DEFAULT_BASELINE_FILE

    create_baseline(
        initial_result.findings,
        baseline_path,
    )

    baseline = load_baseline(baseline_path)

    # Introduce a genuinely new source file containing
    # another detectable compatibility difference.
    new_source = project / "new_example.py"
    new_source.write_text(
        """
        import asyncio

        another_loop = asyncio.get_event_loop()
        """,
        encoding="utf-8",
    )

    second_result = scan(project)

    new_findings, baseline_findings = filter_baseline_findings(
        second_result.findings,
        baseline,
    )

    assert baseline_findings
    assert new_findings

    assert any(
        finding.file.endswith("new_example.py")
        for finding in new_findings
    )