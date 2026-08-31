"""
Scanner and Reporter integration tests.
"""
import json

from pyrift.finding import Finding, Runtime
from pyrift.reporter import to_json, to_markdown, to_text
from pyrift.scanner import ScanResult, scan, scan_file
from pyrift.targets import PythonVersion, TargetConfig


class TestScanner:
    def test_scan_file_returns_findings(self, tmp_path):
        f = tmp_path / "sample.py"
        f.write_text("import ctypes\nctypes.CDLL('foo')\n")
        findings = scan_file(f)
        assert isinstance(findings, list)

    def test_scan_directory(self, tmp_path):
        (tmp_path / "a.py").write_text("e.add_note('x')\n")
        (tmp_path / "b.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert isinstance(result, ScanResult)
        assert result.files_scanned == 2

    def test_score_is_100_for_clean_code(self, tmp_path):
        (tmp_path / "clean.py").write_text("x = 1 + 1\n")
        result = scan(tmp_path)
        assert result.score == 100

    def test_score_decreases_with_errors(self, tmp_path):
        (tmp_path / "bad.py").write_text("e.add_note('x')\n")
        result = scan(tmp_path)
        assert result.score < 100

    def test_skips_venv_dirs(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "noise.py").write_text("e.add_note('x')\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert result.files_scanned == 1

    def test_syntax_error_file_reported(self, tmp_path):
        (tmp_path / "broken.py").write_text("def foo(\n")
        findings = scan_file(tmp_path / "broken.py")
        assert any(f.rule_id == "PARSE" for f in findings)


class TestReporter:
    def _result(self, tmp_path):
        (tmp_path / "t.py").write_text("e.add_note('x')\n")
        return scan(tmp_path)

    def test_json_is_valid(self, tmp_path):
        data = json.loads(to_json(self._result(tmp_path)))
        assert "summary" in data
        assert "findings" in data

    def test_markdown_contains_header(self, tmp_path):
        assert "# pyrift" in to_markdown(self._result(tmp_path))

    def test_text_output_contains_score(self, tmp_path):
        txt = to_text(self._result(tmp_path))
        assert "Score" in txt or "score" in txt

    def test_clean_result_text(self, tmp_path):
        (tmp_path / "c.py").write_text("x = 1\n")
        result = scan(tmp_path)
        assert "No issues" in to_text(result)


class TestProjectTargeting:
    def test_requires_python_suppresses_future_cpython_finding(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'requires-python = ">=3.10,<3.14"\n'
        )
        (tmp_path / "sample.py").write_text(
            "import asyncio\n"
            "asyncio.get_event_loop()\n"
        )

        result = scan(tmp_path)

        assert not any(
            finding.rule_id == "CPY038"
            for finding in result.findings
        )

    def test_requires_python_keeps_affected_cpython_finding(
        self,
        tmp_path,
    ):
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'requires-python = ">=3.10,<3.14"\n'
        )
        (tmp_path / "sample.py").write_text(
            "import datetime\n"
            "datetime.datetime.utcnow()\n"
        )

        result = scan(tmp_path)

        assert any(
            finding.rule_id == "CPY036"
            for finding in result.findings
        )

    def test_no_project_config_keeps_all_findings(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'requires-python = ">=3.10,<3.14"\n'
        )
        (tmp_path / "sample.py").write_text(
            "import asyncio\n"
            "asyncio.get_event_loop()\n"
        )

        result = scan(
            tmp_path,
            use_project_config=False,
        )

        assert any(
            finding.rule_id == "CPY038"
            for finding in result.findings
        )

    def test_explicit_target_overrides_project_config(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[project]\n"
            'requires-python = ">=3.10,<3.14"\n'
        )
        (tmp_path / "sample.py").write_text(
            "import asyncio\n"
            "asyncio.get_event_loop()\n"
        )

        result = scan(
            tmp_path,
            target_config=TargetConfig(
                minimum=PythonVersion.parse("3.14"),
                maximum=PythonVersion.parse("3.14"),
            ),
        )

        assert any(
            finding.rule_id == "CPY038"
            for finding in result.findings
        )


class TestRuntimeTargeting:
    def _write_mixed_runtime_case(self, tmp_path):
        py_file = tmp_path / "mixed.py"
        py_file.write_text(
            "import gc\n"
            "gc.collect()\n"
            "\n"
            "import datetime\n"
            "datetime.datetime.utcnow()\n"
        )
        return py_file

    def test_cpython_runtime_keeps_cpython_findings(self, tmp_path):
        self._write_mixed_runtime_case(tmp_path)

        result = scan(
            tmp_path,
            target_config=TargetConfig(
                runtime=Runtime.CPYTHON,
            ),
        )

        rule_ids = {finding.rule_id for finding in result.findings}

        assert "CPY036" in rule_ids
        assert not any(
            finding.rule_id.startswith("PPY")
            for finding in result.findings
        )

    def test_pypy_runtime_keeps_pypy_findings(self, tmp_path):
        self._write_mixed_runtime_case(tmp_path)

        result = scan(
            tmp_path,
            target_config=TargetConfig(
                runtime=Runtime.PYPY,
            ),
        )

        rule_ids = {finding.rule_id for finding in result.findings}

        assert "PPY010" in rule_ids or "PPY049" in rule_ids
        assert not any(
            finding.rule_id.startswith("CPY")
            for finding in result.findings
        )

    def test_both_runtime_keeps_both_runtime_findings(self, tmp_path):
        self._write_mixed_runtime_case(tmp_path)

        result = scan(
            tmp_path,
            target_config=TargetConfig(
                runtime=Runtime.BOTH,
            ),
        )

        rule_ids = {finding.rule_id for finding in result.findings}

        assert "CPY036" in rule_ids
        assert "PPY010" in rule_ids or "PPY049" in rule_ids

    def test_runtime_filter_applies_before_rule_execution(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("x = 1\n")

        calls = []

        class FakeRule:
            rule_id = "FAKE"
            runtime = Runtime.PYPY
            category = "compatibility"

            def check(self, node, filename, target_config=None):
                calls.append(self.rule_id)
                return []

        result = scan(
            tmp_path,
            rules=[FakeRule()],
            target_config=TargetConfig(
                runtime=Runtime.CPYTHON,
            ),
        )

        assert result.findings == []
        assert result.rule_errors == []
        assert calls == []


def test_scan_reports_rule_execution_errors(tmp_path):
    class BrokenRule:
        rule_id = "TEST-BROKEN"
        runtime = Runtime.CPYTHON
        category = "compatibility"

        def check(self, node, filename, target_config=None):
            raise RuntimeError("boom")

    (tmp_path / "sample.py").write_text("x = 1\n")
    result = scan(tmp_path, rules=[BrokenRule()])

    assert len(result.rule_errors) == 1
    assert "TEST-BROKEN" in result.rule_errors[0]
    assert "RuntimeError" in result.rule_errors[0]


def test_json_includes_evidence_metadata():
    finding = Finding(
        file="example.py",
        line=10,
        rule_id="CPY051",
        runtime=Runtime.CPYTHON,
    )

    result = ScanResult(
        [finding],
        files_scanned=1,
    )

    output = to_json(result)

    assert '"evidence_type": "pep"' in output
    assert '"evidence_source": "pep:703"' in output


def test_markdown_includes_confidence_and_evidence():
    finding = Finding(
        file="example.py",
        line=10,
        rule_id="CPY051",
        runtime=Runtime.CPYTHON,
    )

    result = ScanResult(
        [finding],
        files_scanned=1,
    )

    output = to_markdown(result)

    assert "**Confidence:** `medium`" in output
    assert "**Evidence:** `pep` (`pep:703`)" in output
    assert "**Intent basis:** `documented`" in output


class TestScanResultRepr:
    def test_repr_basic(self):
        result = ScanResult(findings=[], files_scanned=5)
        r = repr(result)
        assert "ScanResult" in r
        assert "5" in r

    def test_repr_with_baseline_suppressed(self):
        result = ScanResult(
            findings=[],
            files_scanned=3,
            baseline_suppressed=2,
        )
        r = repr(result)
        assert "baseline suppressed" in r
        assert "2" in r

    def test_score_with_findings(self):
        from pyrift.finding import Severity

        errors = [
            Finding(
                file="f.py",
                line=1,
                col=0,
                rule_id="CPY001",
                title="t",
                description="d",
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
            )
            for _ in range(3)
        ]
        result = ScanResult(findings=errors, files_scanned=10)
        assert result.score == max(0, 100 - 3 * 10 - 0 * 3)

    def test_score_zero_floor(self):
        from pyrift.finding import Severity

        errors = [
            Finding(
                file="f.py",
                line=1,
                col=0,
                rule_id="CPY001",
                title="t",
                description="d",
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
            )
            for _ in range(20)
        ]
        result = ScanResult(findings=errors, files_scanned=10)
        assert result.score == 0

    def test_scan_single_py_file(self, tmp_path):
        """Scanner accepts a single .py file, not just directories."""
        py_file = tmp_path / "example.py"
        py_file.write_text("import cgi\n")
        result = scan(py_file)
        assert result.files_scanned == 1

    def test_scan_single_non_py_file(self, tmp_path):
        """Scanner skips non-.py files when given directly."""
        txt_file = tmp_path / "example.txt"
        txt_file.write_text("import cgi\n")
        result = scan(txt_file)
        assert result.files_scanned == 0


class TestScannerEdgeCases:
    def test_unicode_decode_error_skipped(self, tmp_path):
        """Files with invalid UTF-8 are skipped gracefully."""
        bad_file = tmp_path / "bad_encoding.py"
        bad_file.write_bytes(
            b"x = 1\n\xff\xfe invalid bytes\n"
        )
        result = scan(tmp_path)
        assert result is not None

    def test_parse_error_reported_as_finding(self, tmp_path):
        """Files with syntax errors produce a PARSE finding."""
        bad_file = tmp_path / "syntax_error.py"
        bad_file.write_text("def broken(\n")
        result = scan(tmp_path)
        parse_findings = [
            f for f in result.findings
            if f.rule_id == "PARSE"
        ]
        assert len(parse_findings) == 1