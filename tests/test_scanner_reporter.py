"""
Scanner and Reporter integration tests.
"""
import json

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

def test_scan_reports_rule_execution_errors(tmp_path):
    class BrokenRule:
        rule_id = "TEST-BROKEN"

        def check(self, node, filename):
            raise RuntimeError("boom")

    (tmp_path / "sample.py").write_text("x = 1\n")
    result = scan(tmp_path, rules=[BrokenRule()])

    assert len(result.rule_errors) == 1
    assert "TEST-BROKEN" in result.rule_errors[0]
    assert "RuntimeError" in result.rule_errors[0]
