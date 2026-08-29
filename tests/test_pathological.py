"""
Tests for pathological / edge-case repositories.

Verifies that pyrift handles unusual files gracefully — either
scanning them successfully or failing safely without crashes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pyrift.scanner import scan, scan_file


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


class TestEmptyFile:
    def test_empty_file_scans_safely(self, tmp_dir: Path) -> None:
        f = tmp_dir / "empty.py"
        f.write_bytes(b"")
        result = scan_file(f)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_empty_file_via_scan(self, tmp_dir: Path) -> None:
        f = tmp_dir / "empty.py"
        f.write_bytes(b"")
        result = scan(tmp_dir, use_project_config=False)
        assert result.files_scanned == 1


class TestOnlyComments:
    def test_comment_only_file(self, tmp_dir: Path) -> None:
        f = tmp_dir / "comments.py"
        f.write_text(
            "# This is a comment\n# Another comment\n",
            encoding="utf-8",
        )
        result = scan_file(f)
        assert isinstance(result, list)


class TestOnlyDocstring:
    def test_docstring_only_file(self, tmp_dir: Path) -> None:
        f = tmp_dir / "docstring.py"
        f.write_text(
            '"""Module docstring."""\n',
            encoding="utf-8",
        )
        result = scan_file(f)
        assert isinstance(result, list)


class TestDeepNesting:
    def test_deeply_nested_code(self, tmp_dir: Path) -> None:
        f = tmp_dir / "deep.py"
        lines = ["def f():\n"]
        indent = "    "

        for i in range(12):
            lines.append(f"{indent * (i + 1)}if True:\n")

        lines.append(f"{indent * 13}pass\n")
        f.write_text("".join(lines), encoding="utf-8")

        result = scan_file(f)
        assert isinstance(result, list)


class TestLongLines:
    def test_very_long_line(self, tmp_dir: Path) -> None:
        f = tmp_dir / "longline.py"
        long_str = 'x = "' + "a" * 1200 + '"\n'
        f.write_text(long_str, encoding="utf-8")

        result = scan_file(f)
        assert isinstance(result, list)


class TestMixedLineEndings:
    def test_mixed_crlf_lf(self, tmp_dir: Path) -> None:
        f = tmp_dir / "mixed.py"
        content = "x = 1\r\ny = 2\nz = 3\r\n"
        f.write_bytes(content.encode("utf-8"))

        result = scan_file(f)
        assert isinstance(result, list)

    def test_all_crlf(self, tmp_dir: Path) -> None:
        f = tmp_dir / "crlf.py"
        f.write_bytes(b"x = 1\r\ny = 2\r\n")

        result = scan_file(f)
        assert isinstance(result, list)

    def test_all_cr(self, tmp_dir: Path) -> None:
        f = tmp_dir / "cr.py"
        f.write_bytes(b"x = 1\ry = 2\r")

        result = scan_file(f)
        assert isinstance(result, list)


class TestNullBytes:
    def test_file_with_null_bytes(self, tmp_dir: Path) -> None:
        f = tmp_dir / "null.py"
        f.write_bytes(b"x = 1\x00\x00y = 2\n")

        result = scan_file(f)

        assert isinstance(result, list)
        assert result
        assert result[0].rule_id == "PARSE"
        assert result[0].severity.value == "error"


class TestSyntaxErrors:
    def test_incomplete_syntax(self, tmp_dir: Path) -> None:
        f = tmp_dir / "syntax_err.py"
        f.write_text("def f(\n", encoding="utf-8")

        result = scan_file(f)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].rule_id == "PARSE"
        assert result[0].severity.value == "error"

    def test_invalid_indentation(self, tmp_dir: Path) -> None:
        f = tmp_dir / "indent_err.py"
        f.write_text(
            "x = 1\n    y = 2\n",
            encoding="utf-8",
        )

        result = scan_file(f)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].rule_id == "PARSE"

    def test_mismatched_parens(self, tmp_dir: Path) -> None:
        f = tmp_dir / "paren_err.py"
        f.write_text(
            "x = (1 + 2\n",
            encoding="utf-8",
        )

        result = scan_file(f)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].rule_id == "PARSE"


class TestManyEmptyFiles:
    def test_directory_with_empty_files(self, tmp_dir: Path) -> None:
        pkg = tmp_dir / "emptypkg"
        pkg.mkdir()

        (pkg / "__init__.py").write_text("", encoding="utf-8")

        for i in range(12):
            (pkg / f"mod_{i:02d}.py").write_bytes(b"")

        result = scan(pkg, use_project_config=False)

        assert result.files_scanned == 13
        assert isinstance(result.findings, list)
        assert isinstance(result.rule_errors, list)


class TestUnicodeIdentifiers:
    def test_unicode_variable_names(self, tmp_dir: Path) -> None:
        f = tmp_dir / "unicode.py"
        f.write_text(
            "# coding: utf-8\n"
            "\u03b1 = 1\n"
            "\u03b2 = 2\n"
            "result = \u03b1 + \u03b2\n",
            encoding="utf-8",
        )

        result = scan_file(f)
        assert isinstance(result, list)


class TestDirectoryScan:
    def test_scan_directory_with_mix(self, tmp_dir: Path) -> None:
        pkg = tmp_dir / "mixed"
        pkg.mkdir()

        (pkg / "__init__.py").write_text(
            '"""Init."""\n',
            encoding="utf-8",
        )
        (pkg / "good.py").write_text(
            "x = 1\n",
            encoding="utf-8",
        )
        (pkg / "empty.py").write_bytes(b"")
        (pkg / "syntax.py").write_text(
            "def f(\n",
            encoding="utf-8",
        )
        (pkg / "nulls.py").write_bytes(b"x\x00y\n")

        result = scan(pkg, use_project_config=False)

        assert result.files_scanned == 5
        assert isinstance(result.findings, list)
        assert isinstance(result.rule_errors, list)

        parse_findings = [
            finding
            for finding in result.findings
            if finding.rule_id == "PARSE"
        ]

        assert len(parse_findings) == 2