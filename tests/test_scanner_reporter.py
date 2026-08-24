"""
Scanner and Reporter integration tests.
"""
import json
from pyrift.scanner import scan_file, scan, ScanResult
from pyrift.reporter import to_json, to_markdown, to_text


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