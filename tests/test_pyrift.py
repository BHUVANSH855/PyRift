"""
pyrift test suite
~~~~~~~~~~~~~~~~~
Run with:  pytest tests/ -v
"""
import ast
import textwrap
import json
import pytest
from pathlib import Path

from pyrift.finding import Severity, Runtime
from pyrift.scanner import scan_file, scan, ScanResult
from pyrift.rules.cpython.cpy001_dict_ordering    import DictOrderingRule
from pyrift.rules.cpython.cpy002_exception_notes  import ExceptionNotesRule
from pyrift.rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule
from pyrift.rules.pypy.ppy001_gc_finalizer        import GcFinalizerRule
from pyrift.rules.pypy.ppy002_ctypes              import CtypesRule
from pyrift.reporter import to_json, to_markdown, to_text


def parse(src: str) -> ast.AST:
    return ast.parse(textwrap.dedent(src))

def run_rule(rule, src: str):
    return rule.check(parse(src), "<test>")


class TestCPY001:
    rule = DictOrderingRule()

    def test_detects_keys_comparison(self):
        findings = run_rule(self.rule, "d = {'a': 1}; assert d.keys() == ['a']")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY001"
        assert findings[0].severity == Severity.WARNING

    def test_detects_values_comparison(self):
        findings = run_rule(self.rule, "d = {'a': 1}; assert d.values() == [1]")
        assert len(findings) == 1

    def test_clean_code_no_finding(self):
        findings = run_rule(self.rule, "assert set(d.keys()) == {'a'}")
        assert len(findings) == 0

    def test_finding_has_suggestion(self):
        findings = run_rule(self.rule, "d.items() == [('a', 1)]")
        if findings:
            assert findings[0].suggestion != ""


class TestCPY002:
    rule = ExceptionNotesRule()

    def test_detects_add_note(self):
        src = """
            try:
                pass
            except ValueError as e:
                e.add_note("extra context")
                raise
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY002"
        assert findings[0].severity == Severity.ERROR

    def test_clean_code_no_finding(self):
        findings = run_rule(self.rule, "e = ValueError('oops')")
        assert len(findings) == 0

    def test_docs_url_present(self):
        findings = run_rule(self.rule, "e.add_note('note')")
        assert findings[0].docs_url != ""


class TestCPY003:
    rule = UnionTypeSyntaxRule()

    def test_detects_union_in_isinstance(self):
        findings = run_rule(self.rule, "isinstance(x, int | str)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY003"
        assert findings[0].severity == Severity.ERROR

    def test_clean_isinstance_with_tuple(self):
        findings = run_rule(self.rule, "isinstance(x, (int, str))")
        assert len(findings) == 0


class TestPPY001:
    rule = GcFinalizerRule()

    def test_detects_close_in_del(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.file.close()
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"
        assert findings[0].runtime == Runtime.PYPY

    def test_detects_flush_in_del(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.conn.flush()
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 1

    def test_clean_del_no_resource(self):
        src = """
            class MyResource:
                def __del__(self):
                    self.count -= 1
        """
        findings = run_rule(self.rule, src)
        assert len(findings) == 0


class TestPPY002:
    rule = CtypesRule()

    def test_detects_ctypes_cdll(self):
        src = "import ctypes\nlib = ctypes.CDLL('libfoo.so')"
        findings = run_rule(self.rule, src)
        assert any(f.rule_id == "PPY002" for f in findings)

    def test_no_finding_without_import(self):
        findings = run_rule(self.rule, "x = CDLL('foo')")
        assert len(findings) == 0

    def test_cffi_suggestion_present(self):
        src = "import ctypes\nctypes.cast(ptr, ctypes.c_void_p)"
        findings = run_rule(self.rule, src)
        if findings:
            assert "cffi" in findings[0].suggestion.lower()


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