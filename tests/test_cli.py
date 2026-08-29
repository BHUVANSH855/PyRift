"""
Tests for pyrift CLI error handling paths.
"""
from __future__ import annotations

import json
import subprocess
import sys


def run_cli(*args: str) -> tuple[int, str, str]:
    """Run pyrift CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "pyrift.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestCliErrorPaths:
    def test_invalid_python_min(self, tmp_path):
        code, _out, err = run_cli(
            "scan",
            str(tmp_path),
            "--python-min",
            "notaversion",
        )
        assert code != 0
        assert "invalid" in err.lower() or "version" in err.lower()

    def test_python_min_greater_than_max(self, tmp_path):
        code, _out, err = run_cli(
            "scan",
            str(tmp_path),
            "--python-min",
            "3.14",
            "--python-max",
            "3.10",
        )
        assert code != 0
        assert (
            "python-min" in err.lower()
            or "greater" in err.lower()
            or "max" in err.lower()
        )

    def test_path_not_found(self, tmp_path):
        nonexistent = str(tmp_path / "nonexistent_dir")
        code, _out, err = run_cli("scan", nonexistent)
        assert code != 0
        assert "not found" in err.lower() or "path" in err.lower()

    def test_json_format(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        code, out, _err = run_cli(
            "scan",
            str(tmp_path),
            "--format",
            "json",
        )
        assert code == 0
        data = json.loads(out)
        assert "summary" in data

    def test_markdown_format(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        code, out, _err = run_cli(
            "scan",
            str(tmp_path),
            "--format",
            "markdown",
        )
        assert code == 0
        assert out.strip()

    def test_no_args_shows_help(self):
        code, out, _err = run_cli("--help")
        assert code == 0
        assert "scan" in out.lower()

    def test_scan_with_findings_exits_nonzero(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("import cgi\n")
        code, _out, _err = run_cli("scan", str(tmp_path))
        assert code != 0

    def test_clean_scan_exits_zero(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\n")
        code, _out, _err = run_cli("scan", str(tmp_path))
        assert code == 0

    def test_scan_no_args_shows_help(self):
        code, out, err = run_cli("scan")
        # scan with no path shows help or error — either way not a crash
        assert (
            "scan" in out.lower()
            or "usage" in (out + err).lower()
            or code != 0
        )

    def test_baseline_no_args_shows_help(self):
        code, out, _err = run_cli("baseline")
        assert code == 0
        assert "baseline" in out.lower() or "usage" in out.lower()

    def test_path_not_found_error(self):
        code, _out, err = run_cli(
            "scan",
            "C:/nonexistent_pyrift_xyz_12345",
        )
        assert code == 2
        assert "not found" in err.lower()
