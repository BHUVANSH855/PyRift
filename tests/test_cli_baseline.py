import json
from pathlib import Path

import pytest

from pyrift.baseline import DEFAULT_BASELINE_FILE
from pyrift.cli import main
from pyrift.finding import Finding, Runtime, Severity
from pyrift.scanner import ScanResult


def make_finding(
    *,
    file="example.py",
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


def write_python_file(path: Path):
    path.write_text(
        "value = 1\n",
        encoding="utf-8",
    )


class TestBaselineCLI:
    def test_baseline_create_writes_file(
        self,
        tmp_path,
        monkeypatch,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        baseline = tmp_path / ".pyrift-baseline.json"

        monkeypatch.setattr(
            "pyrift.cli.scan",
            lambda *args, **kwargs: ScanResult(
                [make_finding()],
                1,
            ),
        )

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "baseline",
                    "create",
                    str(project),
                    "--output",
                    str(baseline),
                ]
            )

        assert exc.value.code == 0
        assert baseline.exists()

        data = json.loads(
            baseline.read_text(encoding="utf-8")
        )

        assert data["version"] == 1
        assert len(data["findings"]) == 1

    def test_scan_without_baseline_preserves_findings(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        finding = make_finding()

        monkeypatch.setattr(
            "pyrift.cli.scan",
            lambda *args, **kwargs: ScanResult(
                [finding],
                1,
            ),
        )

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                    "--no-baseline",
                ]
            )

        assert exc.value.code == 0

        output = capsys.readouterr().out

        assert "PPY999" in output

    def test_scan_with_baseline_filters_existing_finding(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        baseline = tmp_path / DEFAULT_BASELINE_FILE

        finding = make_finding()

        from pyrift.fingerprint import finding_fingerprint

        baseline.write_text(
            json.dumps(
                {
                    "version": 1,
                    "findings": [
                        finding_fingerprint(finding),
                    ],
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr(
            "pyrift.cli.scan",
            lambda *args, **kwargs: ScanResult(
                [finding],
                1,
            ),
        )

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                ]
            )

        assert exc.value.code == 0

        output = capsys.readouterr().out

        assert "No issues found" in output
        assert "PPY999" not in output

    def test_scan_reports_new_finding_with_baseline(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        baseline = tmp_path / DEFAULT_BASELINE_FILE

        existing = make_finding(
            file="existing.py",
        )
        new = make_finding(
            file="new.py",
        )

        from pyrift.fingerprint import finding_fingerprint

        baseline.write_text(
            json.dumps(
                {
                    "version": 1,
                    "findings": [
                        finding_fingerprint(existing),
                    ],
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr(
            "pyrift.cli.scan",
            lambda *args, **kwargs: ScanResult(
                [existing, new],
                1,
            ),
        )

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                ]
            )

        assert exc.value.code == 0

        output = capsys.readouterr().out

        assert "PPY999" in output
        assert "new.py" in output
        assert "existing.py" not in output

    def test_no_baseline_ignores_existing_baseline(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        baseline = tmp_path / DEFAULT_BASELINE_FILE

        finding = make_finding()

        from pyrift.fingerprint import finding_fingerprint

        baseline.write_text(
            json.dumps(
                {
                    "version": 1,
                    "findings": [
                        finding_fingerprint(finding),
                    ],
                }
            ),
            encoding="utf-8",
        )

        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr(
            "pyrift.cli.scan",
            lambda *args, **kwargs: ScanResult(
                [finding],
                1,
            ),
        )

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                    "--no-baseline",
                ]
            )

        assert exc.value.code == 0

        output = capsys.readouterr().out

        assert "PPY999" in output

    def test_invalid_baseline_exits_with_code_2(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        baseline = tmp_path / DEFAULT_BASELINE_FILE

        baseline.write_text(
            "{invalid",
            encoding="utf-8",
        )

        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                ]
            )

        assert exc.value.code == 2

        error = capsys.readouterr().err

        assert "invalid baseline" in error.lower()

    def test_missing_scan_path_exits_with_code_2(
        self,
        tmp_path,
    ):
        missing = tmp_path / "does-not-exist"

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(missing),
                ]
            )

        assert exc.value.code == 2

    def test_scan_passes_platform_to_scanner(
        self,
        tmp_path,
        monkeypatch,
    ):
        project = tmp_path / "project"
        project.mkdir()

        write_python_file(project / "example.py")

        captured = {}

        def fake_scan(*args, **kwargs):
            captured.update(kwargs)
            return ScanResult([], 1)

        monkeypatch.setattr("pyrift.cli.scan", fake_scan)

        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "scan",
                    str(project),
                    "--platform",
                    "linux",
                    "--no-baseline",
                ]
            )

        assert exc.value.code == 0
        assert captured["target_config"].platform == "linux"
